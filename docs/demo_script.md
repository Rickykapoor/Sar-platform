# SAR Platform Demo Script

[START ON PAGE 1: Submit Transaction]
"Welcome to the SAR Platform. Today we're going to demonstrate how our multi-agent AI pipeline completely automates the investigation of suspicious financial activity."
"I'll start by clicking the 'Structuring Demo' preset button."
[CLICK STRUCTURING DEMO]
"You can see the transaction details populate automatically... this is a wire transfer for $9,800, specifically designed to stay just under the $10,000 reporting threshold."
"I'll click 'Submit to Pipeline'."
[CLICK SUBMIT]
"In the background, our AI ingestion agent is masking PII using Microsoft Presidio, and the system immediately flags the transaction with a 'RED' risk tier."

[NAVIGATE TO PAGE 2: Risk Analysis]
"Let's move to the Risk Analysis page."
[CLICK PAGE 2]
"Here, Agent 2 has scored the transaction at 0.95 out of 1.0. You can see the SHAP explainer bar chart on the right, which shows that the transaction amount and the frequency are the primary drivers of this high score."
"Below that, the system has identified the typology as 'Structuring' with 94% confidence, and highlights the explicit risk signals that our ML models detected."

[NAVIGATE TO PAGE 3: Graph View]
"If we go to the Graph View..."
[CLICK PAGE 3]
"Our Neo4j graph database visualizations load here, showing us the direct relationships between the sender, the receiver, and other historic transactions. This helps investigators visually connect the dots across complex laundering rings."

[NAVIGATE TO PAGE 4: SAR Review]
"Now, let's look at the SAR Review page where the human-in-the-loop steps in."
[CLICK PAGE 4]
"I'll click 'Generate Narrative'."
[CLICK GENERATE NARRATIVE]
"Agent 3 streams the generated SAR narrative directly into the UI. It drafts a comprehensive, FinCEN-ready report detailing the subject, the suspicious activity, and the supporting evidence."
"On the right, Agent 4 has verified all compliance checks—ensuring no critical fields are missing and the narrative format meets regulatory standards."
"As an analyst, I can read the narrative, type my name in the approval box, and click 'Approve and File'."
[TYPE NAME, CLICK APPROVE]
"The case is now officially filed. You can see the confirmation balloons on the screen."

[NAVIGATE TO PAGE 5: Audit Trail]
"Finally, we move to the Audit Trail."
[CLICK PAGE 5]
"For compliance and regulatory review, every single decision made by our AI agents is logged here in detail. You can expand any agent's row to see their specific logic."
"At the very bottom, Agent 5 has securely sealed this entire case state into a final, immutable SHA256 hash. This guarantees cryptographic proof that the data and the AI's conclusions have not been tampered with since the time of filing."

"Thank you, that concludes the SAR Platform demo."
