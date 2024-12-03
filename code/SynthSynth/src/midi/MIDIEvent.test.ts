import { describe, it, expect } from 'vitest';
import { MIDIEvent } from './MIDIEvent';

describe('MIDIEvent Class', () => {

  // Test for fromBytes method
  it('should create a MIDIEvent instance from valid MIDI bytes (Note On message)', () => {
    const bytes = [0x90, 60];
    const event = MIDIEvent.fromBytes(bytes);
    expect(event.channel).toBe(1);
    expect(event.note).toBe(60);
    expect(event.messageType).toBe('Press');
  });

  // Test for fromBytes method
  it('should create a MIDIEvent instance from valid MIDI bytes (Note On message)', () => {
    const bytes = [0x80, 57];
    const event = MIDIEvent.fromBytes(bytes);
    expect(event.channel).toBe(1);
    expect(event.note).toBe(57);
    expect(event.messageType).toBe('Release');
  });

  it('should throw an error for an invalid byte array length', () => {
    const bytes = [0x90]; // Only 1 byte instead of 2
    expect(() => MIDIEvent.fromBytes(bytes)).toThrow('MIDI event must consist of exactly 3 bytes.');
  });

  it('should throw an error for an unsupported MIDI message type', () => {
    const bytes = [0xB0, 60]; // Control Change message (unsupported)
    expect(() => MIDIEvent.fromBytes(bytes)).toThrow(
      'Unsupported MIDI message type: 176'
    );
  });

  // Test for toBytes method
  it('should convert a MIDIEvent instance to raw MIDI bytes (Note On message)', () => {
    const event = new MIDIEvent(1, 60, 'Press');
    const bytes = event.toBytes();
    expect(bytes).toEqual([0x90, 60]);
  });

  it('should correctly handle different channels in the toBytes method', () => {
    const event = new MIDIEvent(5, 64, 'Press');
    const bytes = event.toBytes();
    expect(bytes).toEqual([0x94, 64]); // 0x94 is Note On for channel 5
  });
});
