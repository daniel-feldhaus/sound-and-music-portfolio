<!-- src/routes/+page.svelte -->
<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import FileUploader from '../components/FileUploader.svelte';
    import Visualizer from '../components/Visualizer.svelte';
    import Knob from '../components/Knob.svelte';

    let isPlaying: boolean = false;

    let lowGain: number = 1;
    let midGain: number = 1;
    let highGain: number = 1;

    let frequencyData = {
      low: 0,
      mid: 0,
      high: 0
    };

    let animationFrame: number;



    function handleFileSelected(event: CustomEvent<File>) {
      const file = event.detail;
      // do something with the file
    }



    function handleLowChange(event: CustomEvent<number>) {
      lowGain = event.detail;
      // set low gain
    }

    function handleMidChange(event: CustomEvent<number>) {
      midGain = event.detail;
      // set mid gain
    }

    function handleHighChange(event: CustomEvent<number>) {
      highGain = event.detail;
      // set high gain
    }

    onDestroy(() => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
      // pause audio
    });
  </script>

  <style>
    .controls {
      display: flex;
      justify-content: center;
      gap: 2rem;
      margin-top: 2rem;
      flex-wrap: wrap;
    }

    .knob-container {
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    .knob-label {
      margin-top: 1rem;
      font-weight: bold;
    }

    .player-controls {
      display: flex;
      justify-content: center;
      margin-top: 2rem;
    }

    .play-button {
      padding: 0.75rem 1.5rem;
      background-color: #10b981; /* emerald-500 */
      color: white;
      border: none;
      border-radius: 0.5rem;
      font-size: 1rem;
      cursor: pointer;
      transition: background-color 0.3s;
    }

    .play-button:hover {
      background-color: #059669; /* emerald-600 */
    }
  </style>

  <div class="container mx-auto p-4">
    <h1 class="text-3xl font-bold text-center mb-6">Adaptive Tone Control</h1>

    <FileUploader on:fileSelected={handleFileSelected} />


  </div>
