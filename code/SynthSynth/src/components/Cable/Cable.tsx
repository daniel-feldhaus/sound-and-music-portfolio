import { useEffect, forwardRef, useImperativeHandle, useRef, useState } from 'react';
import './Cable.css';
import { BUFFER_SIZE, SAMPLE_RATE } from '../../config';

interface CableProps {
    sendDataToComputer: (data: number) => void;
}

export interface CableHandle {
    receiveData: (data: number) => void;
}

const Cable = forwardRef<CableHandle, CableProps>(({ sendDataToComputer }, ref) => {
    // Initialize bufferRef with BUFFER_SIZE '0's to simulate an empty Cable
    const bufferRef = useRef<number[]>(Array(BUFFER_SIZE).fill(1));

    // Initialize visualizationData with BUFFER_SIZE '0's
    const [visualizationData, setVisualizationData] = useState<number[]>(Array(BUFFER_SIZE).fill(0));

    // Expose the receiveData method to parent components via ref
    useImperativeHandle(ref, () => ({
        receiveData: (data: number) => {
            // Enqueue data into the buffer
            bufferRef.current.push(data);
            // Ensure buffer does not exceed BUFFER_SIZE by dequeuing the oldest data
            if (bufferRef.current.length > BUFFER_SIZE) {
                sendDataToComputer(bufferRef.current.shift()!);
            }
        },
    }));

    // Process the buffer at the defined communication rate
    useEffect(() => {
        const interval = window.setInterval(() => {
            // Update visualizationData to reflect the current buffer state
            setVisualizationData([...bufferRef.current]);
        }, 1000 / SAMPLE_RATE);

        return () => clearInterval(interval);
    }, []);

    // Determine the SVG dimensions
    const width = 200; // pixels
    const height = 50; // pixels
    const zeroPos = 10;
    const onePos = 40;

    // Generate points for the polyline
    const points = visualizationData
        .map((value, index) => {
            const x = width - (index / (BUFFER_SIZE - 2)) * width;
            // Scale value (0 or 1) to y-axis (invert y-axis for better visualization)
            const y = height - (zeroPos + (onePos - zeroPos) * value);
            return `${x},${y}`;
        })
        .join(' ');

    return (
        <div className="cable-container">
            <svg width={width} height={height} className="cable-svg">
                <polyline
                    points={points}
                    fill="none"
                    stroke="#000"
                    strokeWidth="2"
                />
            </svg>
        </div>
    );
});

export default Cable;
