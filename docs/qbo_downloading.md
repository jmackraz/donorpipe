**Discovery Document for Endpoints**
```json
{  
   "issuer":"https://oauth.platform.intuit.com/op/v1",
   "authorization_endpoint":"https://appcenter.intuit.com/connect/oauth2",
   "token_endpoint":"https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
   "userinfo_endpoint":"https://accounts.platform.intuit.com/v1/openid_connect/userinfo",
   "revocation_endpoint":"https://developer.api.intuit.com/v2/oauth2/tokens/revoke",
   "jwks_uri":"https://oauth.platform.intuit.com/op/v1/jwks",
   "response_types_supported":[  
      "code"
   ],
   "subject_types_supported":[  
      "public"
   ],
   "id_token_signing_alg_values_supported":[  
      "RS256"
   ],
   "scopes_supported":[  
      "openid",
      "email",
      "profile",
      "address",
      "phone"
   ],
   "token_endpoint_auth_methods_supported":[  
      "client_secret_post",
      "client_secret_basic"
   ],
   "claims_supported":[  
      "aud",
      "exp",
      "iat",
      "iss",
      "realmid",
      "sub"
   ]
}
```
***Real Online Donation***

```json
{
    "QueryResponse": {
        "SalesReceipt": [
            {
                "domain": "QBO",
                "sparse": false,
                "Id": "2646",
                "SyncToken": "0",
                "MetaData": {
                    "CreateTime": "2025-06-24T15:44:18-07:00",
                    "LastUpdatedTime": "2025-06-24T15:44:18-07:00"
                },
                "CustomField": [],
                "DocNumber": "9410",
                "TxnDate": "2025-03-01",
                "CurrencyRef": {
                    "value": "USD",
                    "name": "United States Dollar"
                },
                "Line": [
                    {
                        "Id": "1",
                        "LineNum": 1,
                        "Amount": 47.63,
                        "DetailType": "SalesItemLineDetail",
                        "SalesItemLineDetail": {
                            "ServiceDate": "2025-03-01",
                            "ItemRef": {
                                "value": "6",
                                "name": "Online Donations"
                            },
                            "ClassRef": {
                                "value": "3600000000001530078",
                                "name": "30-Program:Kenya:Women's Work Center"
                            },
                            "UnitPrice": 47.63,
                            "Qty": 1,
                            "ItemAccountRef": {
                                "value": "5",
                                "name": "4120 Contributed income:Cash donations by individuals"
                            },
                            "TaxCodeRef": {
                                "value": "NON"
                            }
                        },
                        "CustomExtensions": []
                    },
                    {
                        "Amount": 47.63,
                        "DetailType": "SubTotalLineDetail",
                        "SubTotalLineDetail": {}
                    }
                ],
                "CustomerRef": {
                    "value": "217",
                    "name": "Ruth Smith"
                },
                "FreeFormAddress": false,
                "ShipFromAddr": {
                    "Id": "1280",
                    "Line1": "123 Main Street",
                    "Line2": "Anytown, CA 93999"
                },
                "TotalAmt": 47.63,
                "ApplyTaxAfterDiscount": false,
                "PrintStatus": "NotSet",
                "EmailStatus": "NotSet",
                "BillEmail": {
                    "Address": "Smith@rcn.com"
                },
                "Balance": 0,
                "PaymentMethodRef": {
                    "value": "10",
                    "name": "PayPal"
                },
                "PaymentRefNum": "51339764",
                "DepositToAccountRef": {
                    "value": "100",
                    "name": "1020 Checking"
                }
            }
        ],
        "startPosition": 1,
        "maxResults": 1
    },
    "time": "2026-03-18T18:50:49.933-07:00"
}
```

***Corresponding QBO CSV Report Line***

Donor,Transaction date,Num,Product/Service full name,Amount,REF #,Line created by,Line created date,Item class
Ruth Smith,03/01/2025,9410,Online Donations,47.63,51339764,Jim Mackraz,06/24/2025 03:44:18 PM,Women's Work Center

