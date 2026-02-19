import pandas as pd

# Create dummy test cases
data = {
    'TC_ID': ['TC001', 'TC002', 'TC003'],
    'Test Scenario': ['Verify login', 'Verify logout', 'Verify password reset'],
    'Test steps': ['1. Go to login page\n2. Enter credentials', '1. Click logout', '1. Click forgot password'],
    'Expected Result': ['Success', 'Success', 'Email sent'],
    'Priority': ['Critical', 'Medium', 'High'],
    'Test Type': ['Manual', 'Manual', 'Manual']
}

df = pd.DataFrame(data)

# Create multi-sheet excel
with pd.ExcelWriter('dummy_testcases.xlsx') as writer:
    df.to_excel(writer, sheet_name='Authentication', index=False)
    df.to_excel(writer, sheet_name='User Management', index=False)

print("Created dummy_testcases.xlsx")
