# Reminder-pilot design

## Question

Does an additional confirmation and easy-rescheduling workflow reduce did-not-attend (DNA) outcomes compared with the current standard process?

## Proposed design

Use an individually randomised, two-arm operational pilot when governance and workflow conditions allow:

- control: current reminder process;
- treatment: additional confirmation plus easy rescheduling;
- primary outcome: appointment DNA status;
- analysis: intention-to-treat comparison of proportions;
- allocation: fixed randomisation performed before contact;
- analysis code and exclusions fixed before outcome review.

## Sample-size output

`results/experiment_design.csv` reports a normal-approximation sample size for several assumed relative reductions. The effect sizes are planning assumptions, not model estimates. A large required sample means that a short pilot may be useful for delivery, opt-out, rescheduling, and data-quality checks but may not estimate the primary outcome precisely.

## Guardrails

The pilot should monitor:

- opt-out rate;
- late cancellation rate;
- complaint rate;
- subgroup contact-rate ratio;
- delivery failure;
- staff workload;
- rescheduling completion.

A lower DNA rate is not sufficient if the workflow increases unacceptable contact burden or shifts missed appointments into late cancellations.

## Stop and review conditions

Stop or pause the pilot when:

- communication or consent rules are breached;
- data linkage prevents reliable outcome measurement;
- complaint or opt-out signals cross an agreed level;
- treatment delivery differs materially from the registered process;
- a subgroup receives materially different contact access without an accepted reason.
