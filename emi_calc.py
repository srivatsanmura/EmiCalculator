import gradio as gr
import pandas as pd
import numpy as np


def calculate_emi_or_tenure(calculation_type, principal, rate, tenure=None, emi=None):
    """
    Calculates either EMI or loan tenure and generates an amortization schedule.

    Args:
        calculation_type (str): 'Calculate EMI' or 'Calculate Tenure'.
        principal (float): The loan amount.
        rate (float): The annual interest rate (e.g., 8.5 for 8.5%).
        tenure (int, optional): The loan tenure in years. Used for EMI calculation.
        emi (float, optional): The fixed monthly installment. Used for tenure calculation.

    Returns:
        tuple: A tuple containing a formatted string with the result and the amortization schedule as a pandas DataFrame.
    """
    try:
        # Convert annual rate to monthly rate
        monthly_rate = (rate / 100) / 12
        emi_output = ""

        if calculation_type == 'Calculate EMI':
            num_payments = tenure * 12
            if monthly_rate > 0:
                calculated_emi = (principal * monthly_rate * (1 + monthly_rate) ** num_payments) / (
                            ((1 + monthly_rate) ** num_payments) - 1)
            else:
                calculated_emi = principal / num_payments
            emi_output = f"Your Monthly EMI: ₹{calculated_emi:,.2f}"

        elif calculation_type == 'Calculate Tenure':
            if emi is None or emi <= 0:
                return "Please enter a valid EMI amount to calculate tenure.", pd.DataFrame()
            if monthly_rate <= 0:
                num_payments = principal / emi
                emi_output = f"Your loan will be closed in: {num_payments:,.0f} months"
                calculated_emi = emi
            else:
                if emi <= (principal * monthly_rate):
                    return "The entered EMI is too low to cover the monthly interest. Please increase the EMI.", pd.DataFrame()

                # Formula to calculate number of payments (n) from EMI
                # EMI = [P x R x (1+R)^N] / [(1+R)^N-1]
                # Derived from this: N = log(EMI / (EMI - P*R)) / log(1+R)
                log_numerator = np.log(emi / (emi - principal * monthly_rate))
                log_denominator = np.log(1 + monthly_rate)
                num_payments = log_numerator / log_denominator

                emi_output = f"Your loan will be closed in: {num_payments:,.0f} months ({num_payments / 12:.1f} years)"
                calculated_emi = emi

        else:
            return "Invalid calculation type.", pd.DataFrame()

        # Generate the amortization schedule
        schedule = []
        remaining_balance = principal
        num_payments_rounded = int(np.ceil(num_payments))

        total_interest = 0.0

        for month in range(1, num_payments_rounded + 1):
            interest_paid = remaining_balance * monthly_rate
            principal_paid = min(calculated_emi - interest_paid, remaining_balance)

            if principal_paid < 0:
                principal_paid = calculated_emi  # To handle final payment correctly if it's less than interest

            remaining_balance -= principal_paid

            # Stop if balance is nearly zero to avoid floating point issues
            if remaining_balance <= 0.01:
                remaining_balance = 0

            schedule.append({
                "Month": month,
                "EMI": f"{calculated_emi:,.2f}",
                "Principal Paid": f"{principal_paid:,.2f}",
                "Interest Paid": f"{interest_paid:,.2f}",
                "Remaining Balance": f"{max(remaining_balance, 0):,.2f}"
            })

            total_interest += interest_paid

            if remaining_balance == 0:
                break

        df_schedule = pd.DataFrame(schedule)
        emi_output = emi_output + "\n" + f"Total Interest Payment is : {total_interest:,.0f}"

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
        tenure = gr.Slider(label="Tenure (Years)", minimum=1, maximum=20, step=1, value=5)

    with gr.Row(visible=False) as tenure_row:
        fixed_emi = gr.Number(label="Fixed Monthly EMI (₹)")


    # Event listeners for conditional visibility
    def toggle_inputs(calc_type):
        if calc_type == "Calculate EMI":
            return gr.Row(visible=True), gr.Row(visible=False)
        else:
            return gr.Row(visible=False), gr.Row(visible=True)


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
