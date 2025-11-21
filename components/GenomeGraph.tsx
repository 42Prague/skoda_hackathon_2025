import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { GenomeData, SkillNode, SkillLink } from '../types';

interface GenomeGraphProps {
  data: GenomeData;
  onNodeClick: (node: SkillNode) => void;
}

// Extended interface for simulation nodes to include D3 properties
interface SimulationNode extends SkillNode, d3.SimulationNodeDatum {}

const GenomeGraph: React.FC<GenomeGraphProps> = ({ data, onNodeClick }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const originalSizeRef = useRef<{w: number; h: number} | null>(null);
  const zoomLevelRef = useRef<number>(1);

  useEffect(() => {
    if (!svgRef.current) return;

    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    // Clear previous render
    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3.select(svgRef.current)
      .attr("viewBox", `0 0 ${width} ${height}`)
      .style("max-width", "100%")
      .style("height", "auto");

    // store original size for viewBox-based zooming
    if (!originalSizeRef.current) originalSizeRef.current = { w: width, h: height };

    // Container group - everything will be appended into this so we can zoom/pan it
    const container = svg.append("g").attr("class", "genome-container");

    // Zoom behavior (attach to svg and transform container)
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 6])
      .on("zoom", (event) => {
        container.attr("transform", event.transform.toString());
      });

    svg.call(zoom as any);
    // store zoom behavior for programmatic zoom (zoomIn/zoomOut)
    (svgRef as any).currentZoom = zoom;

    // Color scale based on clusters (using brand colors)
    const color = d3.scaleOrdinal<number, string>()
      .domain([1, 2, 3, 4])
      .range(["#64748b", "#06b6d4", "#10b981", "#a855f7"]); // Slate, Cyan, Emerald, Purple

    // Clone nodes/links to prevent mutation of props by D3
    const nodes: SimulationNode[] = data.nodes.map(d => ({ ...d })) as SimulationNode[];
    // Explicitly cast links to any to avoid TS issues with D3 mutating source/target from string to object
    const links = data.links.map(d => ({ ...d })) as any[];

    // Simulation setup with stronger forces for better spacing
    const simulation = d3.forceSimulation<SimulationNode>(nodes)
      .force("link", d3.forceLink(links).id((d: any) => d.id).distance(150))
      .force("charge", d3.forceManyBody().strength(-800))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide().radius((d: any) => (d as SimulationNode).value * 0.6 + 30).strength(1))
      .force("x", d3.forceX(width / 2).strength(0.05))
      .force("y", d3.forceY(height / 2).strength(0.05))
      .alphaDecay(0.01)
      .velocityDecay(0.3);

    // Draw Links (inside container so they zoom/pan)
    const link = container.append("g")
      .attr("stroke", "#334155")
      .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke-width", (d: any) => Math.sqrt(d.value));

    // Draw Nodes
    const node = container.append("g")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .selectAll("g")
      .data(nodes)
      .join("g")
      .call(drag(simulation) as any)
      .on("click", (event, d) => {
        event.stopPropagation();
        onNodeClick(d);
      });

    // Node Circles (Cell Membrane)
    node.append("circle")
      .attr("r", (d) => 10 + (d.value / 4))
      .attr("fill", (d) => color(d.group))
      .attr("fill-opacity", 0.8)
      .attr("stroke", (d) => d.growth > 0.5 ? "#fff" : "none") // Highlight fast growing skills
      .attr("stroke-dasharray", (d) => d.growth > 0.8 ? "2,2" : "none"); // Mutation marker

    // Node Labels
    node.append("text")
      .text((d) => d.label)
      .attr("x", 12)
      .attr("y", 4)
      .attr("fill", "#e2e8f0")
      .attr("stroke", "none")
      .attr("font-size", "10px")
      .attr("font-family", "monospace");

    // Ticker
    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node
        .attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [data, onNodeClick]);

  // ViewBox-based zoom handlers (centered). This preserves drag/force behavior.
  const zoomIn = () => {
    const svgNode = svgRef.current as any;
    const zoomBehavior = svgNode && (svgRef as any).currentZoom;
    if (!svgNode || !zoomBehavior) return;
    d3.select(svgNode).transition().call((zoomBehavior as any).scaleBy, 1.2);
  };

  const zoomOut = () => {
    const svgNode = svgRef.current as any;
    const zoomBehavior = svgNode && (svgRef as any).currentZoom;
    if (!svgNode || !zoomBehavior) return;
    d3.select(svgNode).transition().call((zoomBehavior as any).scaleBy, 1 / 1.2);
  };

  // Drag behavior
  const drag = (simulation: d3.Simulation<SimulationNode, undefined>) => {
    function dragstarted(event: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      // convert pointer to SVG coordinate space accounting for current zoom transform
      if (svgRef.current) {
        const svgNode = svgRef.current;
        const transform = d3.zoomTransform(svgNode);
        const [px, py] = d3.pointer(event, svgNode);
        const invX = transform.invertX(px);
        const invY = transform.invertY(py);
        event.subject.fx = invX;
        event.subject.fy = invY;
      } else {
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      }
    }

    function dragged(event: any) {
      if (svgRef.current) {
        const svgNode = svgRef.current;
        const transform = d3.zoomTransform(svgNode);
        const [px, py] = d3.pointer(event, svgNode);
        const invX = transform.invertX(px);
        const invY = transform.invertY(py);
        event.subject.fx = invX;
        event.subject.fy = invY;
      } else {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      }
    }

    function dragended(event: any) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    return d3.drag<any, any>()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended);
  }

  return (
    <div className="w-full h-full relative overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50 shadow-2xl">
      <div className="absolute top-4 left-4 z-10 pointer-events-none">
        <h3 className="text-cyan-400 font-mono text-sm tracking-widest">VISUALIZATION: FORCE_DIRECTED</h3>
        <p className="text-xs text-slate-500">INTERACTION: DRAG_NODES // CLICK_FOR_DETAILS</p>
      </div>
      <div className="absolute top-4 right-4 z-20 flex flex-col gap-2 pointer-events-auto">
        <button
          onClick={zoomIn}
          aria-label="Zoom in"
          className="w-10 h-10 bg-slate-800/70 hover:bg-slate-700 text-white rounded-md flex items-center justify-center border border-slate-700 shadow"
        >
          +
        </button>
        <button
          onClick={zoomOut}
          aria-label="Zoom out"
          className="w-10 h-10 bg-slate-800/70 hover:bg-slate-700 text-white rounded-md flex items-center justify-center border border-slate-700 shadow"
        >
          −
        </button>
      </div>

      <svg ref={svgRef} className="w-full h-full cursor-grab active:cursor-grabbing" />
    </div>
  );
};

export default GenomeGraph;