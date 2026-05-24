import time
import unittest
from app.models.aircraft import Aircraft
from app.services.collision import check_collisions
from app.services.simulation import generate_synthetic_aircraft

class TestPerformanceLoad(unittest.TestCase):
    """
    Validates that the O(n^2) collision detection algorithm runs
    comfortably within the 1-second broadcast window, even at max load.
    Target: < 100ms for 100 aircraft.
    """

    def _run_collision_benchmark(self, count: int):
        # Generate synthetic aircraft safely scattered in a wide area
        aircraft_list = generate_synthetic_aircraft(count)
        
        # Warmup (JIT compilation in PyPy if used, caches, etc)
        check_collisions(aircraft_list)

        # Measure 10 runs to get a stable average
        runs = 10
        total_time = 0.0

        for _ in range(runs):
            start = time.perf_counter()
            check_collisions(aircraft_list)
            end = time.perf_counter()
            total_time += (end - start)

        avg_time_ms = (total_time / runs) * 1000
        print(f"\n[LoadTest] {count} aircraft -> {avg_time_ms:.2f} ms per collision check")
        
        # Assert the check is well under our 100ms budget
        self.assertLess(avg_time_ms, 100.0)

    def test_load_25_aircraft(self):
        self._run_collision_benchmark(25)

    def test_load_50_aircraft(self):
        self._run_collision_benchmark(50)

    def test_load_100_aircraft(self):
        self._run_collision_benchmark(100)

if __name__ == '__main__':
    unittest.main()
