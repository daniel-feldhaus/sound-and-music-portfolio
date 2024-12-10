import { forwardRef, useImperativeHandle, useState } from 'react';
import './Computer.css';
import { MIDIEvent } from '../../midi/MIDIEvent'; // Adjust the import path as necessary

export interface ComputerHandle {
    receiveData: (data: number) => void;
}

function convertBitsToByte(bits: number[]): number {
    if (bits.length !== 8) {
        throw new Error("Byte conversion requires 8 bites.");
    }
    let byte = 0;
    for (let i = 0; i < 8; i++) {
        byte |= (bits[i] & 0x01) << i;
    }
    return byte
}

const Computer = forwardRef<ComputerHandle, object>((_props, ref) => {
    const [bitBuffer, setBitBuffer] = useState<number[]>([]);
    const [byteBuffer, setByteBuffer] = useState<number[]>([]);
    const [midiEvents, setMidiEvents] = useState<MIDIEvent[]>([]);

    // Expose the receiveData method to parent components via ref
    useImperativeHandle(ref, () => ({
        receiveData: (data: number) => {
            // Ignore non-event
            if (data && bitBuffer.length === 0) {
                return;
            }
            // Start new event
            if (!data && bitBuffer.length === 0) {
                setBitBuffer([0]);
                return;
            }
            const newBits = [...bitBuffer, data];

            // If in the middle of a byte, collect & continue.
            if (newBits.length < 8) {
                setBitBuffer(newBits);
                return;
            }

            // If at the end of a byte, convert bits to byte
            const newBytes = [...byteBuffer, convertBitsToByte(newBits)]
            // Reset bit buffer for next byte.
            setBitBuffer([]);
            setByteBuffer(newBytes);

            if (newBytes.length == 2) {
                const midiEvent = MIDIEvent.fromBytes(newBytes.slice(0, 2));
                setMidiEvents(prevEvents => [...prevEvents, midiEvent]);
                setByteBuffer([]);
            }
        },
    }));

    return (
        <div className="computer-box">
            <p>Computer</p>
            <div className="data-received">
                <p>Bits Received: {bitBuffer.join(', ')}</p>
                <p>Bytes Received: {byteBuffer.map(b => b.toString(16).padStart(2, '0')).join(' ')}</p>
                <p>MIDI Events Detected:</p>
                <ul>
                    {midiEvents.map((event, index) => (
                        <li key={index}>
                            Channel: {event.channel}, Note: {event.note}, Type: {event.messageType}
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
});

export default Computer;
