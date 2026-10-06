# Business / Training Scenario

## Goal

Build a model that predicts whether a grid may need investigation in a future time window.

The model should use past activity data to predict future activity.

The model must **not claim that the network is congested** unless actual network capacity or congestion data is available.

---

## 1. Select the Training Problem

Choose one primary problem:

* High-activity risk
* Anomalous activity
* Activity drop

The selected problem becomes the model's prediction target.

---

## 2. Define the Prediction Unit

Each prediction is based on:

**Grid + Time Window**

Example:

> Grid A during a 15-minute future window.

---

## 3. Define the Time Boundary

The model uses only information available up to time **t**.

```text
Past / Observed                 Future / Predicted

[t-k ─────────────── t]   →   [t+1 ─────────── t+h]
       Features                    Target
```

**Features:** Activity information from the trailing window ending at `t`.

**Target:** The outcome in the future window starting at `t+1`.

---

## 4. Define the Target

The target must describe a **future outcome**.

For example:

> Predict whether activity in the next time window will be unusually high.

If a threshold is used to create the label, clearly document it as a **training proxy**.

Example:

> Activity ≥ X → positive training label.

This label should not be described as proof of actual network congestion.

---

## 5. Model Prediction

The model receives features available at time `t` and predicts the likelihood of the selected condition occurring at `t+1`.

```text
Past Activity
     ↓
Features at t
     ↓
    Model
     ↓
Future Risk at t+1
```

---

## 6. Business Action

The model's output should support the action:

> **Investigate the grid and time window.**

The model should **not** say:

* "The network is congested."
* "The network has insufficient capacity."
* "This location is definitely congested."

Without capacity or congestion ground-truth data, these claims are not supported.

---

## 7. Data Leakage Prevention

The main rule is:

> **Features stop at `t`; the target starts at `t+1`.**

This prevents future information from being used to make the prediction.

```text
          FEATURE WINDOW
       ┌─────────────────┐
       │ Past activity   │
       └────────┬────────┘
                │
                t
                │
          ──────┼──────
                │
              t+1
                │
       ┌────────▼────────┐
       │ FUTURE TARGET   │
       │ Predicted       │
       └─────────────────┘
```

---

## Final Model Definition

> **Using activity information available up to time `t`, predict whether a defined activity condition will occur in the next time window (`t+1`) for a specific grid cell. If the predicted risk is high, the business action is to investigate. The model does not claim actual network congestion unless appropriate capacity or congestion data supports that claim.**
