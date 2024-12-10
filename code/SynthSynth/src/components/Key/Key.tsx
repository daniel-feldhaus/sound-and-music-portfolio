import React, { useRef } from 'react';
import './Key.css';
import { MIDIEvent } from '../../midi/MIDIEvent';

interface KeyProps {
    label: string;
    midiNum: number;
    handleSendSignal: (event: MIDIEvent) => Promise<void>;
}

const Key: React.FC<KeyProps> = ({ label, midiNum, handleSendSignal }) => {
    const isPressedRef = useRef<boolean>(false);
    const isClickedRef = useRef<boolean>(false);
    const isInteractableRef = useRef<boolean>(true);


    // Send a keypress MIDI event.
    const handleKeyPress = async (note: number) => {
        if (!isInteractableRef.current) return;
        // Disable the button to prevent multiple presses
        isPressedRef.current = true;
        isClickedRef.current = true;
        isInteractableRef.current = false;
        await handleSendSignal(new MIDIEvent(1, note, 'Press'));
        if (!isClickedRef.current) {
            isPressedRef.current = false;
            await handleSendSignal(new MIDIEvent(1, note, 'Release'));
        }
        isInteractableRef.current = true;

    }

    // Send a key release MIDI event.
    const handleKeyRelease = async () => {
        isClickedRef.current = false;
        if (!isInteractableRef.current || !isPressedRef.current) return;

        isInteractableRef.current = false;
        await handleSendSignal(new MIDIEvent(1, midiNum, 'Release'));
        isPressedRef.current = false;
        isInteractableRef.current = true;
    }

    return (
        <button
            className={`key-button ${isPressedRef.current ? 'pressed' : ''}`}
            onMouseDown={async () => await handleKeyPress(midiNum)}
            onMouseUp={async () => await handleKeyRelease()}
        >
            {label}
        </button >
    );
};

export default Key;
