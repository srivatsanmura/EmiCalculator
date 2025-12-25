import gradio as gr
import pandas as pd
import numpy as np


def calculate_emi_value(principal: float, rate: float, tenure_years: int) -> float:
    """Calculates the monthly EMI."""
    monthly_rate = (rate / 100) / 12
    num_payments = tenure_years * 12
    
    if monthly_rate > 0:
        return (principal * monthly_rate * (1 + monthly_rate) ** num_payments) / (
                ((1 + monthly_rate) ** num_payments) - 1)
    else:
        return principal / num_payments


def calculate_tenure_value(principal: float, rate: float, emi: float) -> float:
    """Calculates the number of months required to pay off the loan."""
    monthly_rate = (rate / 100) / 12
    
    if monthly_rate <= 0:
        return principal / emi
        
    if emi <= (principal * monthly_rate):
        raise ValueError("The entered EMI is too low to cover the monthly interest.")

    # Formula: N = log(EMI / (EMI - P*R)) / log(1+R)
    log_numerator = np.log(emi / (emi - principal * monthly_rate))
    log_denominator = np.log(1 + monthly_rate)
    return log_numerator / log_denominator


def generate_amortization_schedule(principal: float, rate: float, emi: float, num_payments: int) -> tuple[pd.DataFrame, float]:
    """Generates the amortization schedule and total interest."""
    monthly_rate = (rate / 100) / 12
    schedule = []
    remaining_balance = principal
    total_interest = 0.0
    num_payments_rounded = int(np.ceil(num_payments))

    for month in range(1, num_payments_rounded + 1):
        interest_paid = remaining_balance * monthly_rate
        principal_paid = min(emi - interest_paid, remaining_balance)

        if principal_paid < 0:
             # Should not happen if EMI > Interest, but safe guard
            principal_paid = emi 

        remaining_balance -= principal_paid

        # Stop if balance is nearly zero
        if remaining_balance <= 0.01:
            remaining_balance = 0

        schedule.append({
            "Month": month,
            "EMI": f"{emi:,.2f}",
            "Principal Paid": f"{principal_paid:,.2f}",
            "Interest Paid": f"{interest_paid:,.2f}",
            "Remaining Balance": f"{max(remaining_balance, 0):,.2f}"
        })

        total_interest += interest_paid

        if remaining_balance == 0:
            break
            
    return pd.DataFrame(schedule), total_interest


def calculate_emi_or_tenure(calculation_type, principal, rate, tenure=None, emi=None):
    """
    Main handler for EMI or Tenure calculation.
    """
    try:
        if principal <= 0 or rate < 0:
             return "Error: Principal must be positive and Rate cannot be negative.", pd.DataFrame()

        emi_output = ""
        calculated_emi = 0.0
        num_payments = 0.0

        if calculation_type == 'Calculate EMI':
            if not tenure or tenure <= 0:
                 return "Error: Please enter a valid tenure.", pd.DataFrame()
            
            calculated_emi = calculate_emi_value(principal, rate, tenure)
            num_payments = tenure * 12
            emi_output = f"Your Monthly EMI: ₹{calculated_emi:,.2f}"

        elif calculation_type == 'Calculate Tenure':
            if not emi or emi <= 0:
                return "Please enter a valid EMI amount to calculate tenure.", pd.DataFrame()
            
            try:
                num_payments = calculate_tenure_value(principal, rate, emi)
            except ValueError as e:
                return str(e), pd.DataFrame()
                
            calculated_emi = emi
            emi_output = f"Your loan will be closed in: {num_payments:,.0f} months ({num_payments / 12:.1f} years)"

        else:
            return "Invalid calculation type.", pd.DataFrame()

        # Generate schedule
        df_schedule, total_interest = generate_amortization_schedule(principal, rate, calculated_emi, num_payments)
        emi_output += f"\nTotal Interest Payment is : {total_interest:,.0f}"

        return emi_output, df_schedule

    except (ValueError, TypeError, ZeroDivisionError) as e:
        return f"Error: Please enter valid numerical values. {str(e)}", pd.DataFrame()


# Gradio interface definition
with gr.Blocks(title="EMI and Amortization Calculator") as demo:
    gr.Markdown("## EMI and Amortization Calculator")
    gr.Markdown("Choose whether to calculate the EMI or the loan tenure.")

    with gr.Row():
        calculation_type = gr.Radio(
            ["Calculate EMI", "Calculate Tenure"],
            label="Calculation Type",
            value="Calculate EMI"
        )

    with gr.Row():
        principal = gr.Number(label="Loan Amount (₹)", value=500000)
        rate = gr.Number(label="Annual Interest Rate (%)", value=8.5)

    # Conditional inputs based on calculation type
    with gr.Row() as emi_row:
        tenure = gr.Slider(label="Tenure (Years)", minimum=1, maximum=30, step=1, value=5)

    with gr.Row(visible=False) as tenure_row:
        fixed_emi = gr.Number(label="Fixed Monthly EMI (₹)")


    # Event listeners for conditional visibility
    def toggle_inputs(calc_type):
        if calc_type == "Calculate EMI":
            return gr.update(visible=True), gr.update(visible=False)
        else:
            return gr.update(visible=False), gr.update(visible=True)


    calculation_type.change(toggle_inputs, calculation_type, [emi_row, tenure_row])

    calculate_btn = gr.Button("Calculate", variant="primary")

    emi_output = gr.Text(label="Result", lines=2)
    df_schedule = gr.Dataframe(label="Amortization Schedule")

    # Connect button to the main function
    calculate_btn.click(
        calculate_emi_or_tenure,
        inputs=[calculation_type, principal, rate, tenure, fixed_emi],
        outputs=[emi_output, df_schedule]
    )

demo.launch()
