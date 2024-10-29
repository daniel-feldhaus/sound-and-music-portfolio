/** Some knobs! Full disclosure, chatGPT was pretty much entire responsible for this file.*/
<script lang="ts">
    import { createEventDispatcher } from 'svelte';

    export let value: number = 0;
    export let min: number = 0;
    export let max: number = 100;
    export let size: number = 150; // Diameter in pixels
    export let step: number = 1; // Optional: Implement step functionality if needed

    const dispatch = createEventDispatcher();

    let isDragging = false;
    let rotation = 0;
    let startY = 0;
    let startValue = 0;

    const rotRange = 270; // Degrees
    const startRotation = -135; // Degrees

    // Combine reactive declarations
    $: normalizedValue = Math.min(startRotation + rotRange, Math.max(startRotation, ((value - min) / (max - min)) * rotRange + startRotation));

    function clamp(num: number, min: number, max: number) {
      return Math.max(min, Math.min(num, max));
    }

    function handlePointerDown(event: PointerEvent) {
      isDragging = true;
      startY = event.clientY;
      startValue = value;
      window.addEventListener('pointermove', handlePointerMove);
      window.addEventListener('pointerup', handlePointerUp);
    }

    function handlePointerMove(event: PointerEvent) {
      if (!isDragging) return;
      const deltaY = startY - event.clientY;
      const deltaValue = (deltaY / 100) * (max - min);
      let newValue = clamp(startValue + deltaValue, min, max);

      // Implement step functionality
      newValue = Math.round(newValue / step) * step;

      if (newValue !== value) {
        dispatch('change', newValue);
      }
    }

    function handlePointerUp() {
      isDragging = false;
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
    }
  </script>

  <style>
    .knob-container {
      position: relative;
      touch-action: none;
    }

    .knob-base {
      fill: #ddd;
      stroke: #bbb;
      stroke-width: 2;
    }

    .knob-indicator {
      stroke: #333;
      stroke-width: 4;
      stroke-linecap: round;
    }

    .knob-center {
      fill: #fff;
      stroke: #bbb;
      stroke-width: 2;
    }
  </style>

  <div
    class="knob-container"
    style="width: {size}px; height: {size}px;"
    on:pointerdown={handlePointerDown}
  >
    <svg width="{size}" height="{size}">
      <circle
        class="knob-base"
        cx="{size / 2}"
        cy="{size / 2}"
        r="{size / 2 - 10}"
      />
      <line
        class="knob-indicator"
        x1="{size / 2}"
        y1="{size / 2}"
        x2="{size / 2 + (size / 2 - 20) * Math.cos((normalizedValue - 90) * Math.PI / 180)}"
        y2="{size / 2 + (size / 2 - 20) * Math.sin((normalizedValue - 90) * Math.PI / 180)}"
      />
      <circle
        class="knob-center"
        cx="{size / 2}"
        cy="{size / 2}"
        r="10"
      />
    </svg>
  </div>
