# ModuleTwo acceptance checklist

Status: **not yet performed on physical hardware**. Automated simulator results do not change this status.

Record integration version, Home Assistant version, battery firmware, map version, standalone/cluster configuration, time and results. Do not publish the battery's address or diagnostics without reviewing their contents.

1. Disconnect other Modbus tools and competing power controllers. Enable the Home Assistant control source. For a cluster, use its Auto leader.
2. Install and configure the integration. Confirm it creates one device and does not change the existing setpoint. Compare SOC, measured power, current limits and stored energy with the MyGrid app.
3. Confirm power sign: positive for charging, negative for discharging. Verify lifetime counters and energy/capacity scale with known values; on a cluster, establish which energy values are aggregated before using whole-house statistics.
4. Explicitly request a small allowed setpoint, for example **+100 W** if the live charge limit permits it. Confirm the number readback, then wait a few seconds and check measured power/status. Test **−100 W** only if discharge is allowed.
5. Write **0 W** explicitly to return to idle and verify readback. Do not rely on unloading or disconnection to idle the battery.
6. Briefly interrupt connectivity. Confirm entities become unavailable and recover on polling, and no old command is replayed. Do not induce hardware faults or thermal/voltage limits to test diagnostics; simulator tests cover those cases.
7. Reconfigure to an alternative valid address spelling if available. Verify entity IDs and history remain unchanged and there is no second-client rejection.
8. Verify lifetime charged/discharged entities can be selected for battery storage in the Energy dashboard. Allow Home Assistant time to generate statistics.
9. Change polling and reload/unload the entry. Check that power is not changed. After unloading the last Home Assistant consumer, a separate test client should be able to connect; disconnect it before enabling the integration again. If another Home Assistant consumer still holds the shared endpoint, it should remain connected.
10. Optional: enable the Restart entity and press it only during a suitable maintenance window. Confirm one restart and eventual read recovery; a missing acknowledgment must not cause another restart.

A successful test report should include observations and failures, not just checked boxes. Never assume undocumented firmware fallback behavior.
