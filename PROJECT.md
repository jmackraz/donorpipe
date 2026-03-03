# Project - DonorPipe

## Overview:
A responsive web app that views interelated financial transactions of different types.  The app makes no changes to
the transaction data.
* The app will be support multiple organizational 'accounts' each with their own credentials and repository read-only 
transaction data.
* It will be engineered to production quality, but is only intended for private and demonstration use
* Adequate authenetication and authorization will be needed, at the data layer, before it's deployed with live data
* At the outset, we will not be concerned with account status or settings.

The backend constructs a graph of linked transaction records, and the client displays filtered records listings, detail
views and relationships.

## Key Assumptions:
* The entire transaction graph of any account can be constructed in memory
* The graph can be transmitted to the client in a single GET request
* The web-based clients can manage all the data in memory

## Backend:
The backend is built upon pre-existing python code that ingests a repository of exported CSV reports from several
transaction processing services, and constructs an object graph representing the transaction records and their linking
relationships.

## Front End:
A React/TypeScript web application that works on mobile, but will most often be used on a larger screen, benefiting from a
side-to-side comparative view of selected transaction listings.

Much of the functionality will be filtering transaction listings by a variety of conditions, which will be
done client-side.

## API:
* Simple REST API
* No state changed of primary data
* Key GET method downloads entire transaction graph
* Anticipate clients refreshing the data, or themselves, and will require durable references to individual transactions 
in an attempt to restore UI (selected transaction) state.

An open question is what approach to use for encoding and decoding the graph for transfer.  There are 0,1,many linking 
relationships in the data.  I have very limited experience with this, but I know some solutions can be overly complex.

## Miscellaneous script:
We anticipate adding various CLI utilities, some serving as data review or as an alternative terminal=based UI.

## Requirements:
* All code will be typed
* All new code will be tested

## To be determined (incomplete list):
* Simple and flexible library dependencies are to be selected for templating, infrastructure, etc.
* API infrastructure - e.g. Flask now with an eye to AWS API Gateway in the future
* Graph encoding/decoding solution as mentioned in API

