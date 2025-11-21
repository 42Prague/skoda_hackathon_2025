import html
from textwrap import wrap
from typing import Dict, Any, Literal, Optional, List

import pygraphviz as pgv
from IPython.display import SVG, display

from .data_extractor import DataExtractor


class ITRoadmapper:
    """
    Render a skill/role roadmap (nodes/edges JSON) to SVG using Graphviz (pygraphviz).

    Expected JSON structure (as consumed by `build_roadmap`):

    {
        "meta": {
            "personal_number": int,
            "target_role": "string",
            ...
        },
        "nodes": [
            {
                "id": "string",
                "label": "string",
                "type": "role" | "skill",
                "topics": ["string", ...],          # optional, mainly for skill nodes
                "tools": ["string", ...],           # optional
                "course_keywords": ["string", ...]  # optional, not used in renderer here
            },
            "edges": [
                { "source": "string", "target": "string" }
            ]
        ]
    }

    Notes
    -----
    - This class is purely a renderer: it receives an already generated roadmap JSON
      and produces an SVG using Graphviz via `pygraphviz`.
    - Logic that *builds* the roadmap (calling LLM, etc.) lives outside this class.
    - For skill nodes, the renderer may call `DataExtractor` to suggest internal/external
      courses based on the listed `tools`.
    """

    def __init__(self) -> None:
        """Initialize the renderer (no configuration is stored at instance level)."""
        # Intentionally stateless; all configuration is passed to `build_roadmap`.
        pass

    def build_roadmap(
        self,
        roadmap_json_data: Dict[str, Any],
        data_extractor: DataExtractor,
        roadmap_direction: Literal["LR", "RL", "TB", "BT"],
        edge_line_color: str,
        edge_line_width: float,
        edge_line_style: Literal["ortho", "spline", "line", "polyline"],
        edge_arrow_size: float,
        node_shape: str,
        role_node_fill_color: str,
        role_node_border_color: str,
        skill_node_fill_color: str,
        skill_node_border_color: str,
        background_color: str,
        text_size: int,
        text_font: str,
        text_color: str,
        draw: bool,
        save_path: Optional[str],
    ) -> Dict[str, Any]:
        """
        Render the given roadmap JSON to SVG and optionally display/save it.

        Parameters
        ----------
        roadmap_json_data : dict
            Roadmap data with keys {"meta", "nodes", "edges"}; see class docstring.
            - `nodes` must contain unique "id" values and valid "type" fields
              ("role" or "skill").
            - `edges` must reference existing node ids in "source" and "target".
        data_extractor : DataExtractor
            Instance used to look up internal and external courses for skill nodes.
            In the current implementation, tools from a skill node are used as
            keywords for matching courses.
        roadmap_direction : {'LR', 'RL', 'TB', 'BT'}
            Graph orientation:
            - 'LR' : left-to-right
            - 'RL' : right-to-left
            - 'TB' : top-to-bottom
            - 'BT' : bottom-to-top
        edge_line_color : str
            Edge color (e.g. '#000000').
        edge_line_width : float
            Edge stroke width (e.g. 1.5).
        edge_line_style : {'ortho', 'spline', 'line', 'polyline'}
            Edge routing style used by Graphviz.
        edge_arrow_size : float
            Arrowhead size (typical values are between 0.5 and 1.5).
        node_shape : str
            Graphviz node shape (e.g. 'folder', 'box', 'ellipse').
        role_node_fill_color : str
            Fill color for nodes with type 'role'.
        role_node_border_color : str
            Border color for nodes with type 'role'.
        skill_node_fill_color : str
            Fill color for nodes with type 'skill'.
        skill_node_border_color : str
            Border color for nodes with type 'skill'.
        background_color : str
            Graph background color.
        text_size : int
            Base font size for node labels.
        text_font : str
            Font family for node text (e.g. 'Helvetica').
        text_color : str
            Font color for node text.
        draw : bool
            If True, display the SVG inline (e.g. in Jupyter) via `IPython.display.SVG`.
        save_path : str or None
            If provided, also write the SVG to this file path (e.g. 'roadmap.svg').

        Returns
        -------
        dict
            Dictionary with two keys:
            - "svg_str": str
                SVG markup of the rendered graph.
            - "roadmap_json": dict
                The original `roadmap_json_data` passed in.

        Raises
        ------
        KeyError
            If required keys are missing from nodes or edges (e.g. 'id', 'source', 'target').
        """

        def _html_label(node: Dict[str, Any]) -> str:
            """
            Build an HTML-like label for a node (title + optional details).

            For skill nodes, the label may include:
            - Topics list
            - Tools list
            - Course suggestions derived from tools via `DataExtractor`

            Parameters
            ----------
            node : dict
                Single node object with fields 'label', 'type', and optional 'topics',
                'tools', 'course_keywords'.

            Returns
            -------
            str
                HTML-like label string suitable for Graphviz 'label=<...>' usage.
            """

            def wrap_left(s: str) -> str:
                """
                Wrap a string into multiple left-aligned <BR> lines.

                Long lines are broken on whitespace, preserving existing whitespace
                as much as possible, and HTML-escaped before being embedded.
                """
                lines = wrap(
                    s,
                    break_long_words=False,
                    replace_whitespace=False,
                )
                return "<BR ALIGN=\"LEFT\"/>".join(html.escape(x) for x in lines)

            # Title line (node label)
            title = wrap_left(str(node.get("label", "")))
            body_pt = max(8, text_size - 2)

            rows: List[str] = [
                f'<TR><TD ALIGN="CENTER"><B>{title}</B></TD></TR>'
            ]

            # Skills: topics, tools + suggested courses
            if node.get("type") == "skill":
                topics = [x for x in (node.get("topics") or []) if x]
                tools = [x for x in (node.get("tools") or []) if x]
                # course_keywords = [x for x in (node.get("course_keywords") or []) if x]
                # (currently unused here, but reserved for future tuning of course lookup)

                if topics:
                    rows.append(
                        f'<TR><TD ALIGN="LEFT">'
                        f'<FONT POINT-SIZE="{body_pt}"><I>Topics:</I></FONT>'
                        f'</TD></TR>'
                    )
                    for t in topics:
                        rows.append(
                            f'<TR><TD ALIGN="LEFT">'
                            f'<FONT POINT-SIZE="{body_pt}">{wrap_left(str(t))}</FONT>'
                            f'</TD></TR>'
                        )

                if tools:
                    tools_line = " / ".join(str(t) for t in tools)
                    rows.append(
                        f'<TR><TD ALIGN="LEFT">'
                        f'<FONT POINT-SIZE="{body_pt}"><I>Tools:</I> {wrap_left(tools_line)}</FONT>'
                        f'</TD></TR>'
                    )

                    # First try internal courses; if none, fall back to external.
                    courses = data_extractor.internal_courses(tools) or data_extractor.external_courses(tools)
                    if courses:
                        rows.append(
                            f'<TR><TD ALIGN="LEFT">'
                            f'<FONT POINT-SIZE="{body_pt}"><I>Courses:</I></FONT>'
                            f'</TD></TR>'
                        )
                        for course in courses:
                            rows.append(
                                f'<TR><TD ALIGN="LEFT">'
                                f'<FONT POINT-SIZE="{body_pt}">{wrap_left(str(course))}</FONT>'
                                f'</TD></TR>'
                            )

            table = (
                '<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">'
                + "".join(rows) +
                "</TABLE>"
            )
            # Graphviz HTML-like labels must be wrapped with angle-brackets.
            return f"<{table}>"

        # --- Graph configuration ---
        graph = pgv.AGraph(directed=True, strict=False)

        graph.graph_attr.update(
            rankdir=roadmap_direction,
            splines=edge_line_style,
            nodesep="0.45",
            ranksep="0.65",
            bgcolor=background_color,
        )

        graph.node_attr.update(
            shape=node_shape,
            style="rounded,filled",
            fontsize=text_size,
            fontname=text_font,
            fontcolor=text_color,
        )

        graph.edge_attr.update(
            arrowsize=edge_arrow_size,
            penwidth=edge_line_width,
            color=edge_line_color,
            arrowhead="vee",
        )

        # --- Add nodes ---
        for node in roadmap_json_data["nodes"]:
            is_role = (node.get("type") == "role")
            attrs = {
                "fillcolor": role_node_fill_color if is_role else skill_node_fill_color,
                "color": role_node_border_color if is_role else skill_node_border_color,
            }
            graph.add_node(node["id"], label=_html_label(node), **attrs)

        # --- Add edges ---
        for edge in roadmap_json_data["edges"]:
            graph.add_edge(edge["source"], edge["target"])

        # --- Layout and render ---
        graph.layout(prog="dot")
        svg_bytes = graph.draw(format="svg", prog="dot")
        svg_str = svg_bytes.decode("utf-8")

        if draw:
            display(SVG(svg_str))
        if save_path:
            graph.draw(save_path, prog="dot")

        return {
            "svg_str": svg_str,
            "roadmap_json": roadmap_json_data,
        }