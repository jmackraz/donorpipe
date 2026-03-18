# PayPal API / Downloader

## Goal
1. Write an automated downloader of PayPal reports, using their API in the same general way as `warehouse/downloads/stripe.py`
2. Generate a CSV file that is as close as possible to the original manually-downloaded report, as found in `testdata/Paypal`

**Auth:**
PayPal uses OAuth2.0.  The credentials are in environment variables: PAYPAL_CLIENT_ID and PAYPAL_SECRET_KEY


**PAYPAL DOWNLOAD REPORT HEADERS**
"Date","Time","TimeZone","Name","Type","Status","Currency","Gross","Fee","Net","From Email Address","To Email Address","Transaction ID","Shipping Address","Address Status","Item Title","Item ID","Shipping and Handling Amount","Insurance Amount","Sales Tax","Option 1 Name","Option 1 Value","Option 2 Name","Option 2 Value","Reference Txn ID","Invoice Number","Custom Number","Quantity","Receipt ID","Balance","Address Line 1","Address Line 2/District/Neighborhood","Town/City","State/Province/Region/County/Territory/Prefecture/Republic","Zip/Postal Code","Country","Contact Phone Number","Subject","Note","Country Code","Balance Impact"


**CSV FIELDS USED**

'Type'
'Net'
'Date'
'Name'
'Balance Impact'
'Transaction ID'
'Subject'
'Note'
'From Email Address'
'Reference Txn ID'


**PayPal Transaction Event Codes:** https://developer.paypal.com/docs/transaction-search/transaction-event-codes/


**Example Response:**
The following response includes 3 transactions: donation, partner fee, withdrawal

```json
{
    "transaction_details": [
        {
            "transaction_info": {
                "paypal_account_id": "FAQ4HZUVG7DNL",
                "transaction_id": "25B16188FF732802U",
                "paypal_reference_id": "0CY56775FD262270J",
                "paypal_reference_id_type": "TXN",
                "transaction_event_code": "T0013",
                "transaction_initiation_date": "2025-03-01T15:40:49Z",
                "transaction_updated_date": "2025-03-01T15:40:49Z",
                "transaction_amount": {
                    "currency_code": "USD",
                    "value": "50.00"
                },
                "fee_amount": {
                    "currency_code": "USD",
                    "value": "-1.49"
                },
                "transaction_status": "S",
                "transaction_subject": "donation to Keep Girls in School Project from Smith@rcn.com",
                "ending_balance": {
                    "currency_code": "USD",
                    "value": "48.51"
                },
                "available_balance": {
                    "currency_code": "USD",
                    "value": "48.51"
                },
                "invoice_id": "51339764",
                "protection_eligibility": "02",
                "instrument_type": "PayPal",
                "instrument_sub_type": "PayPal Wallet"
            },
            "payer_info": {
                "account_id": "FAQ4HZUVG7DNL",
                "email_address": "Smith@rcn.com",
                "phone_number": {
                    "country_code": "1",
                    "national_number": "7732744047"
                },
                "address_status": "N",
                "payer_status": "N",
                "payer_name": {
                    "given_name": "Ruth",
                    "surname": "Smith",
                    "alternate_full_name": "Ruth Smith"
                },
                "country_code": "US"
            },
            "shipping_info": {
                "name": "Ruth, Smith"
            },
            "cart_info": {
                "item_details": [
                    {
                        "item_name": "donation to Keep Girls in School Project from Smith@rcn.com",
                        "item_description": "donation to Keep Girls in School Project from Smith@rcn.com",
                        "item_quantity": "1",
                        "item_unit_price": {
                            "currency_code": "USD",
                            "value": "50.00"
                        },
                        "item_amount": {
                            "currency_code": "USD",
                            "value": "50.00"
                        },
                        "total_item_amount": {
                            "currency_code": "USD",
                            "value": "50.00"
                        },
                        "invoice_number": "51339764"
                    }
                ]
            },
            "store_info": {},
            "auction_info": {},
            "incentive_info": {}
        },
        {
            "transaction_info": {
                "transaction_id": "5PU95094C5021335H",
                "paypal_reference_id": "25B16188FF732802U",
                "paypal_reference_id_type": "TXN",
                "transaction_event_code": "T0113",
                "transaction_initiation_date": "2025-03-01T15:40:49Z",
                "transaction_updated_date": "2025-03-01T15:40:49Z",
                "transaction_amount": {
                    "currency_code": "USD",
                    "value": "-0.88"
                },
                "transaction_status": "S",
                "transaction_subject": "donation to Keep Girls in School Project from Smith@rcn.com",
                "ending_balance": {
                    "currency_code": "USD",
                    "value": "47.63"
                },
                "available_balance": {
                    "currency_code": "USD",
                    "value": "47.63"
                },
                "invoice_id": "51339764",
                "protection_eligibility": "02",
                "instrument_type": "PayPal",
                "instrument_sub_type": "PayPal Wallet"
            },
            "payer_info": {
                "address_status": "N",
                "payer_name": {}
            },
            "shipping_info": {},
            "cart_info": {
                "item_details": [
                    {
                        "item_name": "donation to Keep Girls in School Project from Smith@rcn.com",
                        "item_description": "donation to Keep Girls in School Project from Smith@rcn.com",
                        "item_quantity": "1",
                        "invoice_number": "51339764"
                    }
                ]
            },
            "store_info": {},
            "auction_info": {},
            "incentive_info": {}
        },
        {
            "transaction_info": {
                "transaction_id": "45X02981NP708135E",
                "transaction_event_code": "T0403",
                "transaction_initiation_date": "2025-03-01T17:14:58Z",
                "transaction_updated_date": "2025-03-01T17:14:58Z",
                "transaction_amount": {
                    "currency_code": "USD",
                    "value": "-47.63"
                },
                "transaction_status": "S",
                "bank_reference_id": "1040606119578",
                "ending_balance": {
                    "currency_code": "USD",
                    "value": "0.00"
                },
                "available_balance": {
                    "currency_code": "USD",
                    "value": "0.00"
                },
                "protection_eligibility": "02",
                "instrument_type": "PayPal",
                "instrument_sub_type": "PayPal Wallet"
            },
            "payer_info": {
                "address_status": "N",
                "payer_name": {}
            },
            "shipping_info": {},
            "cart_info": {},
            "store_info": {},
            "auction_info": {},
            "incentive_info": {}
        }
    ],
    "account_number": "PQDQXRJFK9ULY",
    "start_date": "2025-02-20T23:59:59Z",
    "end_date": "2025-03-20T00:00:00Z",
    "last_refreshed_datetime": "2026-03-18T17:59:59Z",
    "page": 1,
    "total_items": 3,
    "total_pages": 1,
    "links": [
        {
            "href": "https://api.paypal.com/v1/reporting/transactions?end_date=2025-03-20T00%3A00%3A00.000Z&start_date=2025-02-20T23%3A59%3A59.999Z&fields=transaction_info%2Cpayer_info%2Cshipping_info%2Cauction_info%2Ccart_info%2Cincentive_info%2Cstore_info&page_size=100&page=1",
            "rel": "self",
            "method": "GET"
        }
    ]
}
```