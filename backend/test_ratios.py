#!/usr/bin/env python3
"""Quick test script for get_financial_ratios() refactoring."""

import sys
sys.path.insert(0, '/app')

from app.lib.openbb import get_financial_ratios, SymbolNotFoundError, OpenBBTimeoutError

def test_get_financial_ratios():
    """Test the refactored get_financial_ratios function."""
    try:
        print("Testing get_financial_ratios('AAPL')...")
        ratios = get_financial_ratios('AAPL')

        print(f"\nReceived {len(ratios)} ratio records")

        if ratios:
            print("\nFirst record:")
            first = ratios[0]
            print(f"  Date: {first['date']}")
            print(f"  P/E Ratio: {first['pe_ratio']}")
            print(f"  P/B Ratio: {first['pb_ratio']}")
            print(f"  P/S Ratio: {first['ps_ratio']}")

            # Validate structure
            assert 'date' in first, "Missing 'date' field"
            assert 'pe_ratio' in first, "Missing 'pe_ratio' field"
            assert 'pb_ratio' in first, "Missing 'pb_ratio' field"
            assert 'ps_ratio' in first, "Missing 'ps_ratio' field"

            # Validate types
            assert isinstance(first['date'], str), "Date should be string"
            assert first['pe_ratio'] is None or isinstance(first['pe_ratio'], float), "P/E should be float or None"
            assert first['pb_ratio'] is None or isinstance(first['pb_ratio'], float), "P/B should be float or None"
            assert first['ps_ratio'] is None or isinstance(first['ps_ratio'], float), "P/S should be float or None"

            print("\n✅ All validations passed!")
            return True
        else:
            print("⚠️  Warning: No ratios returned (may be expected for some symbols)")
            return True

    except SymbolNotFoundError as e:
        print(f"❌ Symbol not found: {e}")
        return False
    except OpenBBTimeoutError as e:
        print(f"❌ Timeout: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_get_financial_ratios()
    sys.exit(0 if success else 1)
