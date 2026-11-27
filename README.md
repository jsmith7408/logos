# Project LOGOS

Evidence-gated local applied intelligence research: native reasoning, persistent investigations, bounded workflows, optional local model adapters and explicit uncertainty.

## Latest consolidated source: V6.0 Alpha 0.25

- [Current V6 source](v6/)
- [Versioned release](v6/releases/alpha-0.25/)
- [Installation and use](v6/README.md)
- [Development report](v6/INCREMENT.md)
- [Reflective monitor](v6/reflection.py) and [native research scheduler](v6/research_scheduler.py)
- [Regression tests](v6/test_reflective_scheduler.py)
- [V6 test log](v6/v6_tests_25.txt) and [V5 test log](v6/v5_tests_25.txt)
- [SHA-256 manifest](v6/SHA256SUMS)
- [Original design inputs](v6/design_inputs/)
- [Previous Alpha 0.24](v6/releases/alpha-0.24/) and [original foundation](v6/foundation/)

Alpha 0.25 adds bounded observational monitoring of actual reasoning outcomes and a persistent, explicitly ticked native research scheduler. Seven new tests passed; **126/126 V6 and 70/70 inherited V5 regression executions passed locally**. The monitor does not authenticate evidence or modify facts and rules. Scheduling invokes native investigations only, with no background daemon or external provider calls.

## Limitations

Live offline model validation, external retrieval, general experiment execution, dashboard integration, independent scientific validation and external security certification remain outstanding. Trust policy remains locally configured; source independence is not independently proven. Single-writer prototype; scheduled jobs may repeat after a crash. Telemetry counts events, not distinct reasoning incidents, and the database's physical size is not capped. V5 is owner-authorized, not independently certified. See [V5 acceptance](v5/ACCEPTANCE.md) and [full development report](v6/INCREMENT.md).
