# Relationship display form

In the app detail views, we show directly related transactions. I would like to establish a "canonical form" of
a closed relationship subgraph.  This form should be a directed acyclic graph.

Starting with a transaction of any type (donation, receipt, charge, payout) by traversing relationships we would
typically find:
* 1 payout
* 1,n charges per payout 
* 1 donation per charge 
* 1 receipt per donation (may be missing, may, by a data entry error, be more than 1)

Exceptions:
* Either by latency in the services procssing timeline, or by data-entry or operational error, any of these expected
relationships may be missing.
* Because of data entry error, a donation may have multiple receipts, which is important to reveal


In the web UI, in the detail pane for any type, I'd like display a standard structure, in the same order.
* It starts with payout
* We leave out charge
* 0 or more donations
* For each donation, 0 or more receipts

The displayed structure should contain all types, but the missing entities will be displayed as some sort of placeholder.

The typical number of receipts per donation is 1, but there my be more in important data entry errors.  I want
this display to be simple in the typical 0,1 case and not show "a list with one element."

At some point, we may make the elements in this pane interactive or hoverable, so it's probably wise to isolate the 
mini model and display logic, and any future complexity, into a component if it is not already broken out.