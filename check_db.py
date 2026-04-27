import sqlite3

conn = sqlite3.connect('notebooks/finance_tracker.db')
cursor = conn.cursor()

print('=== SALARY ===')
cursor.execute('SELECT * FROM salary')
print(cursor.fetchall())

print('\n=== EXPENSES ===')
cursor.execute('SELECT * FROM expenses')
print(cursor.fetchall())

print('\n=== INCOME_LOGS ===')
cursor.execute('SELECT * FROM income_logs')
print(cursor.fetchall())

print('\n=== USER_PROFILE ===')
cursor.execute('SELECT * FROM user_profile')
print(cursor.fetchall())

print('\n=== APP_STATE ===')
cursor.execute('SELECT * FROM app_state')
print(cursor.fetchall())

conn.close()
