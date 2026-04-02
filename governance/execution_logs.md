# Execution Logs

Date:
- `2026-04-02`

Status:
- `Phase 3 baseline`

Note:
- The table below mixes controlled validation examples with live tracked run entries.
- The `PK-075` rows are real `2026-04-02` usage evidence from tracked prompt-specialist intake inside canonical runs.

| Scenario | Tier | Model | Input Tokens | Cached Tokens | Output Tokens | Estimated USD | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `router_smoke_test` | `tier_2_mid` | `gpt-5.4-mini` | 120 | 20 | 40 | 0.000197 | Synthetic usage payload from `tests/test_api_router.py` proving model selection, usage recording, and artifact write path. |
| `small_request_routing` | `tier_3_junior` | `gpt-5.4-nano` | 0 | 0 | 0 | 0.000000 | Controlled routing-only validation. |
| `medium_request_routing` | `tier_2_mid` | `gpt-5.4-mini` | 0 | 0 | 0 | 0.000000 | Controlled routing-only validation. |
| `ambiguous_request_routing` | `tier_1_senior` | `gpt-5.4` | 0 | 0 | 0 | 0.000000 | Controlled routing-only validation with approval gate. |
| run_c0450da4dea5 | PK-075 | PromptSpecialist | tier_2_mid | gpt-4.1-mini | 333 | 0 | 156 | 0.000000 | - | agent_json via StudioRoleAgent |
| run_ea0fc32a38f9 | PK-075 | PromptSpecialist | tier_2_mid | gpt-4.1-mini | 333 | 0 | 120 | 0.000000 | - | agent_json via StudioRoleAgent |
| run_ea0fc32a38f9 | PK-112 | Architect | tier_2_mid | gpt-4.1-mini | 989 | 0 | 572 | 0.000000 | - | agent_text via StudioRoleAgent |
| run_fbf89251a3f3 | PK-075 | PromptSpecialist | tier_2_mid | gpt-4.1-mini | 333 | 0 | 128 | 0.000000 | - | agent_json via StudioRoleAgent |
| run_9f11726b433d | PK-116 | PK076-D | tier_3_junior | gpt-5.4-nano | 313 | 0 | 716 | 0.000958 | C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\projects\program-kanban\artifacts\pk076_slice2_registration_path_evidence.md | - |
| run_3357f6f454f5 | PK-116 | PK076-D | tier_3_junior | gpt-5.4-nano | 4839 | 0 | 1962 | 0.003420 | C:\Users\rodne\Dev\_AIStudio_worktrees\studio-control\projects\program-kanban\artifacts\pk076_slice2_registration_path_evidence.md | - |
| run_cccc82b405c6 | PK-117 | pk076e_guarded_redispatch | tier_2_mid | gpt-5.4-mini | 7012 | 0 | 926 | 0.008037 | projects/program-kanban/artifacts/pk076_slice2_registration_propagation.md | PK076-E guarded re-dispatch after missing canonical dispatch record |
| run_9a4a3312232e | PK-117 | pk076e_guarded_implementation_redispatch | tier_2_mid | gpt-5.4-mini | 8273 | 0 | 546 | 0.007843 | projects/program-kanban/artifacts/pk076_slice2_registration_propagation.md | PK076-E guarded re-dispatch with implementation-mode provisioning |
| run_eb8535f400fe | PK-118 | pk076g_guarded_implementation_dispatch | tier_2_mid | gpt-5.4-mini | 8407 | 0 | 519 | 0.007862 | projects/program-kanban/artifacts/pk076_final_operator_wall_visibility.md | PK076-G guarded implementation dispatch for final PK-076 visibility blocker |
