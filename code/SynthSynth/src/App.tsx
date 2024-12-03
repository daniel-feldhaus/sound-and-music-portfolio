import React, { useEffect, useRef, useState } from 'react';
import './App.css';
import Key from './components/Key/Key';
import Cable, { CableHandle } from './components/Cable/Cable';
import Computer, { ComputerHandle } from './components/Computer/Computer';
import { BIT_RATE } from './config';
import { MIDIEvent } from './midi/MIDIEvent';

const App: React.FC = () => {
  const cableRef = useRef<CableHandle>(null);
  const computerRef = useRef<ComputerHandle>(null);
  const [isTransmitting, setIsTransmitting] = useState<boolean>(false);
  // Calculate the waiting duration between key presses in milliseconds
  const BIT_INTERVAL_MS = 1000 / BIT_RATE;


  // Process the buffer at the defined communication rate
  useEffect(() => {
    const interval = window.setInterval(() => {
      if (!isTransmitting) {
        cableRef.current?.receiveData(1);
      }
    }, BIT_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [BIT_INTERVAL_MS, isTransmitting]);

  const handleSendSignal = async (event: MIDIEvent) => {
    const bytes = event.toBytes();
    const bitPromises: Promise<void>[] = []; // Collect promises for all bits

    const sendByteBits = (byte: number, byteIndex: number) => {
      const bits = [];
      for (let i = 0; i < 8; i++) {
        const bit = (byte >> i) & 0x01; // Extract the i-th bit (LSB first)
        bits.push(bit);
      }

      bits.forEach((bit, bitIndex) => {
        const bitSendTime =
          (byteIndex * bits.length + bitIndex) * BIT_INTERVAL_MS;

        // Create a Promise for each bit
        const bitPromise = new Promise<void>((resolve) => {
          setTimeout(() => {
            cableRef.current?.receiveData(bit);
            resolve();
          }, bitSendTime);
        });

        bitPromises.push(bitPromise);
      });
    };

    setIsTransmitting(true);

    bytes.forEach((byte, byteIndex) => {
      sendByteBits(byte, byteIndex);
    });

    // Wait for all bits to be sent
    await Promise.all(bitPromises);

    // Re-enable the button after the last bit has been sent
    setIsTransmitting(false);
  };



  // Handle data received from the Cable
  const handleSendToComputer = (data: number) => {
    computerRef.current?.receiveData(data);
  };


  return (
    <div className="app-container">
      <div className="key-section">
        <Key label="A" midiNum={57} handleSendSignal={handleSendSignal} />
        <Key label="C" midiNum={60} handleSendSignal={handleSendSignal} />
        <Cable ref={cableRef} sendDataToComputer={handleSendToComputer} />
        <Computer ref={computerRef} />
      </div>
    </div>
  );
};

export default App;
