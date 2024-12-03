export type MessageType = 'Press' | 'Release';

export const MESSAGE_TYPES: Record<MessageType, number> = {
  Press: 0x90,
  Release: 0x80
};

export class MIDIEvent {
    channel: number;
    note: number;
    messageType: MessageType;

    /**
     * Initializes a new MIDIEvent instance.
     * @param channel - MIDI channel number (1-16).
     * @param note - MIDI note number (0-127).
     */
    constructor(channel: number, note: number, messageType: MessageType) {
      // Validate MIDI channel (1-16)
      if (channel < 1 || channel > 16) {
        throw new Error(`MIDI channel must be between 1 and 16: ${channel}`);
      }

      // Validate MIDI note number (0-127)
      if (note < 0 || note > 127) {
        throw new Error("MIDI note number must be between 0 and 127.");
      }

      this.channel = channel;
      this.note = note;
      this.messageType = messageType;
    }

    /**
     * Creates a MIDIEvent instance from raw MIDI bytes.
     * @param bytes - Array of MIDI bytes representing the event.
     * @returns A new MIDIEvent instance.
     */
    static fromBytes(bytes: number[]): MIDIEvent {
      if (bytes.length !== 2) {
        throw new Error("MIDI event must consist of exactly 3 bytes.");
      }

      const [status, note] = bytes;

      // Determine message type based on status byte
      const messageType = status & 0xF0; // Upper 4 bits
      const channel = (status & 0x0F) + 1; // Lower 4 bits (0-15) mapped to channels (1-16)

      const messageTypeString = Object.keys(MESSAGE_TYPES).find(key => MESSAGE_TYPES[key as MessageType] === messageType);

      if(!messageTypeString){
        throw new Error(`Unsupported MIDI message type: ${messageType}`);
      }

      // Create and return the MIDIEvent instance
      return new MIDIEvent(channel, note, messageTypeString as MessageType);
    }

    /**
     * Converts the MIDIEvent instance into an array of raw MIDI bytes.
     * @returns An array of MIDI bytes representing the event.
     */
    toBytes(): number[] {

      // MIDI Note On status byte starts at 0x90 for channel 1
      // Each subsequent channel increments the status byte by 1
      const status = MESSAGE_TYPES[this.messageType] + ((this.channel - 1) & 0x0F); // Ensures channel is within 0-15

      return [status, this.note];
    }
  }
