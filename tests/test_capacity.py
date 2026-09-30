def test_capacity_math():
    capacity=100
    going=99
    requested=1
    assert going+requested <= capacity
    assert going+requested == 100

def test_over_capacity():
    assert not (100+1 <= 100)
