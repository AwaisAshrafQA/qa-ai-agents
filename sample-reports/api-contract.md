# API Contract Review

_Model: demo (recorded response)_

## Summary

The ShopLite Orders API has 3 endpoints and a reasonable request schema for POST /orders, but the contract has gaps that let invalid data through and leave error behaviour undefined. GET /orders/{orderId} has no auth and no 404, the cancel endpoint documents no errors or response body, and three string fields have no limits.

## Request Validations

| Endpoint | Field | Rule | Why |
|---|---|---|---|
| POST /orders | items | Required, array, at least 1 item | An order with no items must never be created |
| POST /orders | items[].quantity | Integer >= 1, with an upper limit (e.g. <= 99) | Without a maximum, a huge quantity can break stock and pricing |
| POST /orders | items[].sku | Required string matching the SKU pattern, max 32 characters | Unbounded strings risk injection and log flooding |
| POST /orders | paymentMethod | Required; enum card \| cod; case-sensitive | Unknown payment methods must be rejected before calling the payment provider |
| POST /orders | couponCode | Optional; 6-12 alphanumeric characters | Matches the business rule in SL-101 and blocks malformed codes early |
| POST /orders | deliveryNote | Optional; max 250 characters; strip HTML | Free text shown to couriers is a stored-XSS and size risk |

## Negative Tests

| Endpoint | Title | Request Change | Expected Status | Expected Error |
|---|---|---|---|---|
| POST /orders | Empty items array | items: [] | 400 | items must contain at least 1 item |
| POST /orders | Zero quantity | items[0].quantity: 0 | 400 | quantity must be >= 1 |
| POST /orders | Quantity as a string | items[0].quantity: "2" | 400 | quantity must be an integer |
| POST /orders | Unsupported payment method | paymentMethod: "crypto" | 400 | paymentMethod must be one of card, cod |
| POST /orders | Missing bearer token | Remove the Authorization header | 401 | Authentication required |
| POST /orders | Coupon with special characters | couponCode: "SAVE-20!" | 400 | couponCode has an invalid format |
| GET /orders/{orderId} | Unknown order id | orderId: ord-does-not-exist | 404 | Order not found |
| GET /orders/{orderId} | Another shopper's order | Use a token for user B to read user A's order | 404 | Order not found (do not reveal that it exists) |
| POST /orders/{orderId}/cancel | Cancel a shipped order | Order in status shipped | 409 | Order can no longer be cancelled |

## Schema Checks

| Endpoint | Status | Assertion |
|---|---|---|
| POST /orders | 201 | Body validates against the Order schema; id, status and total are present; status is pending or paid |
| POST /orders | 201 | total is a number >= 0 with 2 decimal places, and currency is a 3-letter ISO code |
| POST /orders | 400 | Error body follows a single error schema (code, message, field) |
| GET /orders/{orderId} | 200 | Body validates against the Order schema, with no extra undocumented fields |
| POST /orders/{orderId}/cancel | 200 | Returns the Order with status cancelled (once the spec documents this) |

## Spec Gaps

| Endpoint | Gap | Risk | Recommendation |
|---|---|---|---|
| GET /orders/{orderId} | no security requirement declared | high | Add bearerAuth and document that shoppers can only read their own orders |
| GET /orders/{orderId} | no 4xx response documented | medium | Document 401 and 404 with the shared error schema |
| POST /orders/{orderId}/cancel | 200 response has no schema | medium | Return the updated Order so clients and tests can assert the new status |
| POST /orders/{orderId}/cancel | no 4xx response documented | medium | Document 401, 404 and 409 (not cancellable) |
| POST /orders | string fields items[].sku, couponCode and deliveryNote have no length, format or pattern | medium | Add maxLength and pattern so the contract enforces the business rules |
| POST /orders | 400 response has no schema | low | Define a reusable Error schema in components and reference it from every 4xx |

## Computed Locally

- **Title:** ShopLite Orders API
- **Version:** 1.4.0
- **Spec Format:** OpenAPI 3.0.3
- **Endpoint Count:** 3
- **Endpoints With Gaps:** 3

### Spec Level Gaps

- no servers defined

### Endpoints

| Endpoint | Summary | Deprecated | Secured | Parameters | Request Fields | Documented Responses | Gaps |
|---|---|---|---|---|---|---|---|
| POST /orders | Create an order from the current cart | no | yes |  | field: items, type: array, required: yes, nullable: no, read_only: no, constraints: minItems: 1; field: items[].sku, type: string, required: yes, nullable: no, read_only: no, constraints: ; field: items[].quantity, type: integer, required: yes, nullable: no, read_only: no, constraints: minimum: 1; field: paymentMethod, type: string, required: yes, nullable: no, read_only: no, constraints: enum: card; cod; field: couponCode, type: string, required: no, nullable: no, read_only: no, constraints: ; field: deliveryNote, type: string, required: no, nullable: no, read_only: no, constraints:  | 201; 400 | no operationId; secured but 401 not documented; array field 'items' has no maxItems; string field 'items[].sku' has no maxLength, format, pattern or enum; string field 'couponCode' has no maxLength, format, pattern or enum; string field 'deliveryNote' has no maxLength, format, pattern or enum |
| GET /orders/{orderId} | Get an order | no | no | path:orderId* |  | 200 | no operationId; no 4xx response documented; no security requirement declared; path parameter 'orderId' has no format, pattern or maxLength |
| POST /orders/{orderId}/cancel | Cancel an order | no | yes | path:orderId* |  | 200 | no operationId; no 4xx response documented; 200 response has no schema; secured but 401 not documented; path parameter 'orderId' has no format, pattern or maxLength |
