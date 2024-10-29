<!-- src/components/Visualizer.svelte -->
<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import * as d3 from 'd3';

    export let frequencyData: { low: number; mid: number; high: number } = {
      low: 0,
      mid: 0,
      high: 0
    };

    let svg: SVGSVGElement;
    const width = 300;
    const height = 150;
    const margin = { top: 20, right: 20, bottom: 30, left: 40 };

    let data = [
      { band: 'Low', value: frequencyData.low },
      { band: 'Mid', value: frequencyData.mid },
      { band: 'High', value: frequencyData.high }
    ];

    $: data = [
      { band: 'Low', value: frequencyData.low },
      { band: 'Mid', value: frequencyData.mid },
      { band: 'High', value: frequencyData.high }
    ];

    onMount(() => {
      const svgElement = d3.select(svg)
        .attr('width', width)
        .attr('height', height);

      const x = d3.scaleBand<string>()
        .domain(data.map(d => d.band))
        .range([margin.left, width - margin.right])
        .padding(0.4);

      const y = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.value) || 100])
        .nice()
        .range([height - margin.bottom, margin.top]);

      const xAxis = (g: d3.Selection<SVGGElement, unknown, null, undefined>) => g
        .attr('transform', `translate(0,${height - margin.bottom})`)
        .call(d3.axisBottom(x));

      const yAxis = (g: d3.Selection<SVGGElement, unknown, null, undefined>) => g
        .attr('transform', `translate(${margin.left},0)`)
        .call(d3.axisLeft(y));

      svgElement.append('g').call(xAxis);
      svgElement.append('g').call(yAxis);

      svgElement.selectAll<SVGRectElement, typeof data[0]>('.bar')
        .data(data)
        .enter()
        .append('rect')
        .attr('class', 'bar')
        .attr('x', d => x(d.band)!)
        .attr('y', d => y(d.value))
        .attr('width', x.bandwidth())
        .attr('height', d => y(0) - y(d.value))
        .attr('fill', '#3b82f6');

      // Update function
      function update() {
        y.domain([0, d3.max(data, d => d.value) || 100]).nice();

        svgElement.selectAll<SVGRectElement, typeof data[0]>('.bar')
          .data(data)
          .join(
            enter => enter.append('rect')
              .attr('class', 'bar')
              .attr('x', d => x(d.band)!)
              .attr('width', x.bandwidth())
              .attr('y', y(0))
              .attr('height', 0)
              .attr('fill', '#3b82f6')
              .call(enter => enter.transition().duration(500)
                .attr('y', d => y(d.value))
                .attr('height', d => y(0) - y(d.value))
              ),
            update => update
              .call(update => update.transition().duration(500)
                .attr('y', d => y(d.value))
                .attr('height', d => y(0) - y(d.value))
              ),
            exit => exit.call(exit => exit.transition().duration(500)
              .attr('y', y(0))
              .attr('height', 0)
              .remove()
            )
          );

        svgElement.select<SVGGElement>('g').call(yAxis);
      }

      // Watch for data changes
      const interval = setInterval(() => {
        update();
      }, 100);

      return () => {
        clearInterval(interval);
      };
    });

    onDestroy(() => {
      // Cleanup if necessary
    });
  </script>

  <svg bind:this={svg}></svg>

  <style>
    .bar {
      transition: fill 0.3s;
    }

    .bar:hover {
      fill: #2563eb; /* blue-600 */
    }

    /* Optional: Add styles for axes */
    .domain {
      stroke: #000;
    }

    .tick line {
      stroke: #ccc;
    }

    .tick text {
      font-size: 12px;
    }
  </style>
