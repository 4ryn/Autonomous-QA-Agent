# E-Shop Product Specifications

## Product Catalog

### Laptop Pro 15
- Product ID: laptop
- Name: Laptop Pro 15
- Description: High-performance laptop for professionals
- Price: $1299.99
- Category: Electronics
- Stock Status: In Stock
- Specifications:
  - Processor: Intel Core i7
  - RAM: 16GB
  - Storage: 512GB SSD
  - Display: 15.6 inch Full HD

### Wireless Mouse
- Product ID: mouse
- Name: Wireless Mouse
- Description: Ergonomic wireless mouse
- Price: $29.99
- Category: Accessories
- Stock Status: In Stock
- Specifications:
  - Connection: Bluetooth 5.0
  - Battery Life: 12 months
  - DPI: 1600
  - Buttons: 6 programmable buttons

### USB-C Cable
- Product ID: cable
- Name: USB-C Cable
- Description: Fast charging USB-C cable
- Price: $15.99
- Category: Accessories
- Stock Status: In Stock
- Specifications:
  - Length: 6 feet
  - Data Transfer: USB 3.1
  - Power Delivery: 100W
  - Compatibility: Universal USB-C devices

## Discount Codes

### Available Discount Codes
1. SAVE15
   - Discount: 15% off entire order
   - Valid: Always active
   - Minimum Order: None
   - Maximum Discount: Unlimited
   - Usage: One per order

### Discount Code Rules
- Only one discount code can be applied per order
- Discount code must be entered in uppercase (SAVE15)
- Invalid codes should display error message: "Invalid discount code"
- Empty discount code field should display: "Please enter a discount code"
- Discount is applied to subtotal before shipping
- Discount code can be applied at any time before payment

## Shipping Options

### Standard Shipping
- Cost: Free
- Delivery Time: 5-7 business days
- Default Option: Yes
- Tracking: Provided
- Coverage: Domestic only

### Express Shipping
- Cost: $10.00
- Delivery Time: 2-3 business days
- Default Option: No
- Tracking: Real-time tracking
- Coverage: Domestic only

### Shipping Calculation Rules
- Shipping cost is added after discount is applied
- Shipping option can be changed before payment
- Default selection is Standard Shipping (Free)
- Express Shipping adds exactly $10.00 to order total

## Payment Methods

### Credit Card
- Supported Cards: Visa, MasterCard, American Express, Discover
- Default Option: Yes
- Processing: Instant
- Additional Fees: None

### PayPal
- Account Required: Yes
- Default Option: No
- Processing: Instant
- Additional Fees: None

## Price Calculation Formula

```
Subtotal = Sum of (Product Price × Quantity) for all items in cart
Discount Amount = Subtotal × Discount Rate (if discount code applied)
Shipping Cost = Selected Shipping Option Cost
Total = Subtotal - Discount Amount + Shipping Cost
```

## Cart Functionality

### Add to Cart
- Each product has an "Add to Cart" button
- Initial quantity when added: 1
- If product already in cart: Quantity increases by 1
- No stock limit checking (unlimited inventory assumed)

### Update Quantity
- Plus (+) button: Increases quantity by 1
- Minus (-) button: Decreases quantity by 1
- If quantity reaches 0: Item is removed from cart
- Quantity display updates in real-time
- Prices recalculate automatically

### Remove from Cart
- Remove button: Completely removes item from cart
- All quantities and prices recalculate immediately
- If cart becomes empty: Display "Your cart is empty"

## Order Processing Rules

### Order Validation
1. Cart must not be empty
2. All required customer fields must be filled:
   - Full Name (required)
   - Email Address (required, must be valid format)
   - Shipping Address (required)
3. Shipping option must be selected (default: Standard)
4. Payment method must be selected (default: Credit Card)

### Order Completion
- On successful validation: Display success message
- Success message: "Order placed successfully! Thank you for your purchase."
- All sections hide after successful order
- Page shows only success message

### Error Handling
- Empty cart: Display alert "Your cart is empty!"
- Invalid form: Display alert "Please fill in all required fields correctly."
- Missing name: Show error "Name is required"
- Invalid email: Show error "Valid email is required"
- Missing address: Show error "Address is required"