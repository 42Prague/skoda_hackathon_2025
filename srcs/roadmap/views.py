import os
import json
import uuid
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from authen.models import Member, Roadmap
from .utils.it_roadmapper import ITRoadmapper
from .utils.ai_module import AIModule
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from django.views import generic
from .forms import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, reverse
from django.http import HttpResponseRedirect
from  .utils.data_service import get_data_extractor

@csrf_exempt
def chat_ai(request, pk):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)
    body = json.loads(request.body)
    user_msg = body.get("message", "")

    # 1. Load stored roadmap JSON using employee/member ID
    roadmap = Roadmap.objects.filter(member_id=pk).first()
    if roadmap is None:
        return JsonResponse({"error": "Roadmap not found for this member"}, status=404)

    roadmap_json = roadmap.json_data    # already a dict from JSONField

    meta = roadmap_json.get("meta", {})
    nodes = roadmap_json.get("nodes", [])

    # 2. Collect ALL SKILL nodes instead of just the first one
    skill_nodes = [n for n in nodes if n.get("type") == "skill"]

    if not skill_nodes:
        return JsonResponse({"error": "No skill nodes found in roadmap JSON"}, status=500)

# Prepare a compact list to place inside the prompt
    skills_summary = [
    {
        "id": n.get("id"),
        "label": n.get("label"),
        "topics": n.get("topics", []),
        "tools": n.get("tools", [])
    }
    for n in skill_nodes
]

    target_role = meta.get("target_role", "")

    system_prompt = f"""
SYSTEM: You are Node Coach — a focused IT skill mentor used by HR and employees for internal learning.
You answer ONLY within the scope of THIS node, and you always reply in a structured,
beautiful “learning card” format using clean Markdown.

NODES (all skill nodes)
{json.dumps(skills_summary, ensure_ascii=False, indent=2)}

CONTEXT
- target_role: "{target_role}"

CONTEXT
- target_role: "Senior Python Developer"

RESPONSE FORMAT (STRICT)
Always respond in well-formatted Markdown, using emoji section headers
and clean bullet/numbered lists. No HTML. No broken formatting.

Your answer must contain exactly these sections in this order:

---

### 1️⃣ Overview
# A short, clear description of what this node teaches and why it matters for the user’s career.

---

### 2️⃣ Key Concepts to Understand
Bullet list of 4–7 practical concepts directly from this node’s topics.

---

### 3️⃣ Official Documentation / Must-Read Links
List only real documentation or safe generic search terms.
➡️ Never invent broken URLs.
If unsure, write: “Search for: *Python lists official docs*”.

---

### 4️⃣ Practical Steps to Start
Concrete 5–8 actionable steps the user can do today.

---

### 5️⃣ Common Mistakes / What to Avoid
Short list of pitfalls related ONLY to this node.

---

### 6️⃣ Mini-Practice Tasks
3–5 small exercises.
Include short runnable code snippets in fenced blocks only when appropriate.

---

### 7️⃣ Extra Tools That Help
List of 3–5 relevant tools (from node.tools or related), each with a 1-line explanation.

---

STYLE RULES
- Always use clean Markdown (### headers, lists, fenced code blocks).
- Keep sections compact, readable, and “study-guide style”.
- Expand only when the user explicitly asks for details, examples, or reasoning.
- Never drift into other nodes or unrelated domains.
- If the user goes off-topic:
  “❗ Out of scope for this node. Here we focus on: <2 relevant topics>.”
- Provide safe, professional guidance; avoid unsafe commands or credentials.

❌ ABSOLUTE PROHIBITION
You must NOT:
- end answers with offers such as “Want a plan?”, “Могу выдать чек-лист?”,
  “Нужны дополнительные материалы?”, “Хочешь продолжение?” or similar.
- propose additional services, extra sections, plans, quizzes, tasks,
  checklists, summaries, study programs, or follow-up actions unless
  the user explicitly asks for them.

You only produce the required structured answer. No invitations, no suggestions.

SESSION BEHAVIOR
- Track what the user already explored in this node.
- Suggest the next logical topics *only inside the given sections* and *never as a closing question*.
"""

    ai = AIModule(
        openai_api_key=settings.OPENAI_API_KEY,
        model="hackathon-gpt-5.1",
        reasoning_effort="none",
        system_prompt=system_prompt
    )

    reply = ai.query(user_msg)

    return JsonResponse({"reply": reply})

def member_dashboard(request, pk):
    
    _ROADMAP_SYSTEM_PROMPT = """
You are an advanced intelligent and wise IT carrier Roadmapper.

INPUT: a JSON describing an employee’s starting skills, and target role.

TASK: Return ONLY valid JSON that encodes a compact, logical skill graph (DAG) for a left-to-right roadmap.

OUTPUT SCHEMA (adhere exactly):
{
    "meta": { "personal_number": int, "target_role": "string" },
    "nodes": [
        {
            "id": "string",
            "label": "string",
            "type": "role|skill",
            "topics": ["string", ...],
            "tools":  ["string", ...]
        }
    ],
    "edges": [ { "source": "string", "target": "string" } ]
}

RULES
- Roadmap starts from the "You are here!" node and ends in "target_role" node. These are ROLE nodes.
- All intermediate nodes are SKILL nodes.

- Each SKILL node represents a compact, meaningful skill area or phase — not a single tutorial topic.
    Example scale: "Data Preparation", "Model Deployment", "Experiment Tracking", "System Design".
    Avoid tiny micro-steps like "write unit tests" or "CLI entry points".

- Each skill node contains:
    - Label — a short name of the skill area (2–5 words, Title Case).
    - Topics — 2–4 concise subskills or learning goals needed to progress to the next phase.
        * Each topic should describe an actionable concept or capability, not a chapter title.
        For example: "feature scaling & encoding", "data versioning & reproducibility",
        "service monitoring & alerting".
    - Tools — optional, 0–3 widely used technologies or frameworks typically applied in this area.
        * Use generic, canonical names only (e.g., "Pandas", "Docker", "PyTorch").
        * If there are no clear common tools, leave this field empty.

- Each skill node:
    - Is always a destination from at least one previous node.
    - Has at least one outgoing edge toward a more advanced or dependent node.
    - Prefer multiple parallel skill branches at the same level (e.g., "Data", "Modeling", "Deployment")
    instead of a single long linear chain.

- The roadmap should be short and readable:
    - Total number of skill nodes ≈ 6–10.
    - Longest path from start to target ≤ 8 edges.

OUTPUT:
Return only the JSON object with fields {meta, nodes, edges}. No prose, no explanations.
"""
    member = get_object_or_404(Member, pk=pk)
    roadmap = getattr(member, "roadmap", None)

    # ---------- File output path ----------
    output_dir = os.path.join(settings.MEDIA_ROOT, "roadmaps")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"roadmap_{uuid.uuid4().hex}.svg")

    # ---------- Detect changes ----------
    member_last_changed = max(
        filter(None, [
            getattr(member, "updated_at", None),
            getattr(member, "modified", None),
            getattr(member, "date_joined", None),
        ]),
        default=timezone.now()
    )

    should_regen = (
        not roadmap
        or roadmap.generated_at < member_last_changed
    )
    de = get_data_extractor()
    if should_regen:
        # === 1) Build user prompt ===
        user_input = {
            "personal_number": member.user.username, #TODO change to "username"
            "target_role": member.target_role or "Senior Developer",
            "skills": de.skills_for_user(int(member.user.pk))
        }
        user_prompt = json.dumps(user_input, indent=2)

        # === 2) Query AI ===
        ai = AIModule(
            openai_api_key=settings.OPENAI_API_KEY,
            model="hackathon-gpt-5.1",
            reasoning_effort="none",
            system_prompt=_ROADMAP_SYSTEM_PROMPT
        )

        raw_json = ai.query(user_prompt)

        
        try:
            roadmap_json_data = json.loads(raw_json)
        except Exception:
            roadmap_json_data = {"meta": {}, "nodes": [], "edges": []}

        # === 3) Generate SVG ===
        roadmapper = ITRoadmapper()

        result = roadmapper.build_roadmap(
            roadmap_json_data=roadmap_json_data,
            data_extractor=de,
            roadmap_direction="LR",
            edge_line_style="ortho",
            edge_line_color="#000000",
            edge_line_width=1.5,
            edge_arrow_size=0.8,
            node_shape="folder",
            role_node_fill_color="#FFB24D",
            role_node_border_color="#1B1B1B",
            skill_node_fill_color="#56C8FD",
            skill_node_border_color="#000000",
            background_color="#ffffff",
            text_size=12,
            text_font="Helvetica",
            text_color="#000000",
            draw=False,
            save_path=output_path,
        )

        # Extract SVG + JSON
        svg_str = result["svg_str"]
        json_data = result["roadmap_json"]

        # === 4) Save to DB ===
        roadmap, _ = Roadmap.objects.update_or_create(
            member=member,
            defaults={
                "svg_path": os.path.join("roadmaps", os.path.basename(output_path)),
                "json_data": json_data,
                "generated_at": timezone.now(),
                "llm_model_used": "gpt-5",
            },
        )

    # === 5) Render SVG ===
    svg_url = f"{settings.MEDIA_URL}{roadmap.svg_path}" if roadmap else None

    return render(
        request,
        "dashboard/member_chart.html",
        {"member": member, "svg_url": svg_url}
    )

class MemberSelfUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "dashboard/member_self_update.html"
    form_class = TargetModelForm
    context_object_name = "member"

    def get_object(self, queryset=None):
        return self.request.user.member

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member"] = self.request.user
        return context

    def form_valid(self, form):
        member = self.request.user.member  # The object being edited
        changed_member = False

        new_value = form.cleaned_data.get("target_role")
        old_value = member.target_role

        if not form.has_changed():
            return redirect(self.get_success_url())

    # Otherwise let UpdateView save normally
        return super().form_valid(form)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "roadmap:career-roadmap",
            kwargs={"pk": self.request.user.member.pk}
        )
