# HERCULES CTF — Challenge Author Guidelines

## 1. Principles of AI-Resilient Challenge Authoring
The HERCULES framework establishes five design principles:
1. **Investigation over Information Retrieval**: Never design challenges where the solution is an answer to a trivia question or a query answerable via standard web search. Supply raw evidence that must be gathered and correlated.
2. **Practical Exploitation over Theoretical Answers**: Demand interaction with running stateful services.
3. **Context-Dependent Reasoning**: Require at least 3-4 independent evidence sources to reach a conclusion.
4. **Controlled Unpredictability**: Utilize instance-specific seed data and dynamic flags where appropriate.
5. **Verifiable Outcomes**: Server-side validation must verify intermediate state transitions, not just client-submitted strings.

## 2. Multi-Stage Challenge Blueprint
Every Hard challenge (450–500 points) should consist of 4–7 distinct stages.
Each stage must:
- Provide clear, unambiguous clues for eliminating decoys.
- Produce an output that directly feeds into the subsequent stage.
- Be solvable without guessing undocumented system behaviors.

## 3. Secret Hygiene Rules
- **Rule 1**: NEVER commit passwords, flags, or private decryption keys to public challenge attachments.
- **Rule 2**: Public evidence should contain realistic decoys with documented historical reasons for rejection (e.g. `SUPERSEDED`, mismatched access roles, incorrect console assignments).
- **Rule 3**: All flags must follow the exact competition regex and include strict character validation.
