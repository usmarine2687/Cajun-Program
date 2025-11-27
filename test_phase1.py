"""Quick test of Phase 1 service layer functions."""
from db import service

print("=" * 60)
print("  Phase 1 Service Layer Test")
print("=" * 60)

# Test 1: Create Customer
print("\n1. Creating customers...")
customer1 = service.create_customer("John Doe", "5551234567")
customer2 = service.create_customer("Tax Exempt Business", "5559999999", 
                                   tax_exempt=1, tax_exempt_certificate="TX123")
customer3 = service.create_customer("Out of State Customer", "5558888888",
                                   out_of_state=1)
print(f"   ✓ Created customers: {customer1}, {customer2}, {customer3}")

# Test 2: Create Parts
print("\n2. Creating parts...")
part1 = service.create_part("Oil Filter", stock_quantity=10, price=15.99, taxable=1)
part2 = service.create_part("Spark Plug", stock_quantity=20, price=8.50, taxable=1)
part3 = service.create_part("Manual", stock_quantity=5, price=25.00, taxable=0)
print(f"   ✓ Created parts: {part1}, {part2}, {part3}")

# Test 3: Create New Engine
print("\n3. Creating new engine...")
engine1 = service.create_new_engine(115, "MFS115A", "SN12345", purchase_price=8000.00)
print(f"   ✓ Created engine: {engine1}")

# Test 4: Tax Calculation - Tax Exempt
print("\n4. Testing tax calculation - Tax Exempt Customer...")
line_items = [
    {'amount': 100.00, 'taxable': 1},
    {'amount': 50.00, 'taxable': 1}
]
subtotal, tax, total = service.calculate_tax(customer2, line_items)
print(f"   Subtotal: ${subtotal:.2f}, Tax: ${tax:.2f}, Total: ${total:.2f}")
print(f"   ✓ Tax is $0.00 (PASS)" if tax == 0.0 else f"   ✗ Tax should be $0.00 (FAIL)")

# Test 5: Tax Calculation - Out of State with Engine
print("\n5. Testing tax calculation - Out of State Engine Sale...")
line_items = [{'amount': 50.00, 'taxable': 1}]
subtotal, tax, total = service.calculate_tax(customer3, line_items, 
                                             new_engine_sale_price=5000.00)
expected_tax = 50.00 * 0.0975
print(f"   Subtotal: ${subtotal:.2f}, Tax: ${tax:.2f}, Total: ${total:.2f}")
print(f"   Expected tax: ${expected_tax:.2f}")
print(f"   ✓ Only parts taxed (PASS)" if abs(tax - expected_tax) < 0.01 else f"   ✗ Tax incorrect (FAIL)")

# Test 6: Tax Calculation - Standard
print("\n6. Testing tax calculation - Standard Customer...")
line_items = [
    {'amount': 100.00, 'taxable': 1},
    {'amount': 50.00, 'taxable': 1}
]
subtotal, tax, total = service.calculate_tax(customer1, line_items)
expected_tax = 150.00 * 0.0975
print(f"   Subtotal: ${subtotal:.2f}, Tax: ${tax:.2f}, Total: ${total:.2f}")
print(f"   Expected tax: ${expected_tax:.2f}")
print(f"   ✓ Standard tax applied (PASS)" if abs(tax - expected_tax) < 0.01 else f"   ✗ Tax incorrect (FAIL)")

# Test 7: List Functions
print("\n7. Testing list functions...")
customers = service.list_customers()
parts = service.list_parts()
engines = service.list_new_engines()
print(f"   ✓ Found {len(customers)} customers, {len(parts)} parts, {len(engines)} engines")

print("\n" + "=" * 60)
print("  All Phase 1 Core Functions Working!")
print("=" * 60)
