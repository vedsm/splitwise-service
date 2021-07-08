# This is a repository for splitwise backend

Follow the Makefile.
```
make run_event_receiver
make package
make publish
make deploy
```

Refer wiki for pipi access token setup->


### Problem Statement :
• Develop a solution for sharing expenses
• User can create an expense with another User and share the expense based on:
Percentage share
• Exact amount of share
• User should be able to view pending balances with other users
• User should be able to record a payment settlement to clear balances with a user.


### User Scenarios (APIs)
* User Signup|Signin
* Create a new expense
  * Req:
    1. Own UserID
    2. Type of share: Percentage|Exact
    3. Other UserIDs involved
  * Receive: Success|Failure
* View pending balances
  * Send:
    1. Own userID
  * Receive: 
    1. [{“userID”:<>, “Gets”:<>, “Receives”:<>}]
* Record Payment settlement
  * Send:
    1. Own user_id
    2. Other user_id
    3. Payment
  * Receive: Success|Failure

### Models
* user
  * user_id
  * name
* expense_master
  * expense_master_id: 
  * type: 0-expense | 1- settlement 
  * amount: 
  * currency: (default rs)
  * created_by:
  * user_ids: []
  * share_type: 0-Percentage | 1. Exact
  * share_division: {}
* expense
  * expense_id:
  * expense_master_id:
  * payer: (user_id)
  * payee: <>
  * amount: <>
  * currency: (default rs)