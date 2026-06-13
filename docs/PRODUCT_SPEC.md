# Product Spec

## Product Name

Drift Store Drops

## Summary

Drift Store Drops is a mobile-first photo catalog for a local thrift/drift store.
Employees can post new arrivals through Telegram, customers can browse by category on the web, and subscribers can receive one notification per published batch.

## Goals

- Make it easy for staff to capture new arrivals fast
- Make it easy for customers to browse on mobile
- Make it easy for the owner/admin to publish a batch
- Reduce friction between "item arrived" and "customer sees it"

## Non-Goals

- No ecommerce checkout
- No online payment handling
- No shipping workflow
- No customer login
- No inventory guarantee
- No sold/hold flow in the MVP

## Primary Users

### Customer

- Opens the site on mobile
- Sees latest arrivals first
- Browses by category
- Opens a drop card
- Uses Call Store or Directions
- Reads the availability disclaimer

### Employee

- Sends a photo to the Telegram bot
- Chooses category
- Enters price or skips
- Enters description or skips
- The drop is saved as a draft

### Admin

- Reviews drafts
- Edits drops
- Publishes a batch
- Archives or deletes drops later
- Manages categories
- Updates store settings

## Core Pages

- Home
- Latest arrivals
- Category view
- Drop detail
- Admin panel

## Content Rules

- A drop may have a photo, category, price, and description
- Price and description are optional
- Every visible item must show the posted date or time context
- Published drops are the only items visible to customers
- Drafts remain hidden from customer-facing pages

## Store Contact Rules

- Call Store should use the store phone number
- If the store is open, the call link should work normally
- If the store is closed, show current hours and timezone instead of pushing the call flow as the primary action
- Directions should open Google Maps

## Notification Rules

- A published batch should trigger one Telegram notification for the batch
- The system should not send one notification per photo for the same batch
- Subscribers only need a simple broadcast message in the MVP

## Statuses

- draft
- published
- archived

## MVP Disclaimers

- Call to confirm availability. Items may sell quickly.

