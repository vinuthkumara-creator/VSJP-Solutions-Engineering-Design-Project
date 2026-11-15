[← Back to README](../README.md)

# Results & Future Work

## Summary of Results

The results were decent. The LoRa network worked fine within the expected range between the sender and receiver, and communication still worked across wall barriers. The free-flow sensing mechanism also works well; a threshold frequency will have to be determined for the detection of system errors for each application. When the flow decreases due to pipe blockage, this is signalled by an increase in frequency, which is displayed on the dashboard.

## Discussion

Temperature and wind could affect the feasibility of the system. Strong wind above the rooftop could change the flow direction and affect the readings of the capacitive sensor. A metal cover around the exposed free flow may therefore be required so that wind does not affect the flow.

## Future Improvements

- Instead of measuring capacitance directly, the free-flow sensing mechanism could be improved with a **differential capacitive measurement circuit**, which accounts for temperature shifts and humidity changes. This would use two capacitors, one outside the flow and one inside the flow. Another measurement circuit that converts the differential capacitance to time was also explored and could improve the current free-flow sensing methodology.
- Integrate the Receiver Module and the flow sensing circuit onto a single PCB to reduce wiring complexity, connector count, and overall form factor.
