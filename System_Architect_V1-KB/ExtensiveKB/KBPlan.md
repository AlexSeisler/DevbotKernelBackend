# Optimized KB Plan

Here’s the new **optimized structure** with security fully integrated:

1. **00_mission.md**
    - One-paragraph operational mandate.
    - Explicit upstream-only role.
    - Always CVL-check before output.
    - Security mindset: scaffold, don’t enforce.
    
    [00_mission.md — System Architect V1 Mission](https://www.notion.so/00_mission-md-System-Architect-V1-Mission-24a128e09c7780c383c6d0d14f5738da?pvs=21)
    
2. **01_role_definition.md**
    - Position in ACS ecosystem.
    - Integration contracts with DevBot, CIAN, SecurityOpsArchitect, AI IDEs.
    - Boundaries + escalation rules.
    
    [01_role_definition.md — System Architect V1 Role Definition](https://www.notion.so/01_role_definition-md-System-Architect-V1-Role-Definition-24a128e09c778028b489c677b74f3dc1?pvs=21)
    
3. **02_build_level_protocols.md**
    - L1–L5 definitions.
    - Security expectations per level.
    - Scaling implications for infra, auth, DB, observability.
    
    [02_build_level_protocols.md](https://www.notion.so/02_build_level_protocols-md-24a128e09c778022b5cbffd5f5b6a45c?pvs=21)
    
4. **03_subsystem_map_reference.md**
    - Expanded list of subsystems (auth, queue, vector, ai, observability, database, infra, frontend/UI, API gateway, testing).
    - Risk tags per subsystem to trigger security scaffolding.
    - Standard tech stacks for each.
5. **04_phase_protocols.md**
    - Each phase as **Input → Process → Output** with decision trees.
    - Security injection points.
    - Re-planning triggers.
6. **05_input_processing.md**
    - Rules for normalizing goals, requirements, and semantic graphs.
    - Missing context detection.
    - Validation before planning starts.
7. **06_task_queue_emission.md**
    - Full emission rules:
        - Priority scoring logic.
        - Dependency resolution.
        - Token optimization.
        - CVL validation before queue insertion.
8. **07_monitoring_and_adaptation.md**
    - Live tracking protocol.
    - Drift/error detection.
    - Repo re-ingestion and adaptive re-planning workflow.
9. **08_security_scaffolding.md**
    - Triggers from subsystem mapping + planning phases.
    - STRIDE/DREAD/OWASP alignment.
    - Output format for security milestones.
10. **09_security_milestone_templates.md**
    - Pre-made milestone templates with phase hooks.
    - Required_by field for SecurityOpsArchitect handoff.
11. **10_prompt_templates.md**
    - Modular prompts for diagnostics, planning, security checks, and confirmations.
    - Conditional branching prompts.
12. **11_tooling_reference.md**
    - Aligned with subsystems.
    - Recommended tooling per build level.