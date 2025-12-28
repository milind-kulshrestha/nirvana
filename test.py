import pprint
from openbb import obb
result = obb.equity.price.quote(symbol='AAPL', provider='fmp')
pprint.pprint(result)