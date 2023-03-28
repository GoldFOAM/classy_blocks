import unittest

import numpy as np

from classy_blocks.items.vertex import Vertex

from classy_blocks.construct import edges
from classy_blocks.items.edges.edge import Edge
from classy_blocks.items.edges.arcs.arc import ArcEdge
from classy_blocks.items.edges.arcs.origin import OriginEdge, arc_from_origin
from classy_blocks.items.edges.arcs.angle import AngleEdge, arc_from_theta
from classy_blocks.items.edges.spline import SplineEdge, PolyLineEdge
from classy_blocks.items.edges.project import ProjectEdge
from classy_blocks.items.edges.factory import factory

from classy_blocks.util import functions as f

class EdgeTransformTests(unittest.TestCase):
    """Transformations of all edge types"""
    def setUp(self):
        self.vertex_1 = Vertex([0, 0, 0], 0)
        self.vertex_2 = Vertex([1, 0, 0], 1)

    def test_arc_edge_translate(self):
        arc_edge = ArcEdge(self.vertex_1, self.vertex_2, edges.Arc([0.5, 0, 0]))
        
        arc_edge.translate([1, 1, 1])
        np.testing.assert_array_equal(arc_edge.data.point, [1.5, 1, 1])

    def test_angle_edge_rotate_1(self):
        angle_edge = AngleEdge(
            self.vertex_1, self.vertex_2,
            edges.Angle(np.pi/2, [0, 0, 1])
        )

        angle_edge.rotate(np.pi/2, [0, 0, 1], [0, 0, 0])

        np.testing.assert_array_equal(
            angle_edge.data.axis, [0, 0, 1])

        self.assertEqual(angle_edge.data.angle, np.pi/2)

    def test_angle_edge_rotate_2(self):
        angle_edge = AngleEdge(
            self.vertex_1, self.vertex_2,
            edges.Angle(np.pi/2, [0, 0, 1])
        )

        angle_edge.rotate(np.pi/2, [1, 0, 0], [0, 0, 0])

        np.testing.assert_array_equal(
            angle_edge.data.axis, [0, -1, 0])

        self.assertEqual(angle_edge.data.angle, np.pi/2)

    def test_spline_edge_translate(self):
        spline_edge = SplineEdge(
            self.vertex_1, self.vertex_2,
            edges.Spline([
                [0.25, 0.1, 0],
                [0.5, 0.5, 0],
                [0.75, 0.1, 0],
            ])
        )

        spline_edge.translate([1, 1, 1])
    
        np.testing.assert_array_equal(
            spline_edge.data.points, [
                [1.25, 1.1, 1],
                [1.5, 1.5, 1],
                [1.75, 1.1, 1],
            ]
        )

class EdgeFactoryTests(unittest.TestCase):
    """Factory tests: edge creation"""
    def setUp(self):
        self.vertex_1 = Vertex([0, 0, 0], 0)
        self.vertex_2 = Vertex([1, 0, 0], 1)

    def test_arc(self):
        arc_point = [0.5, 0.2, 0]

        edg = factory.create(self.vertex_1, self.vertex_2, edges.Arc(arc_point))

        self.assertIsInstance(edg, ArcEdge)
        np.testing.assert_array_almost_equal(arc_point, edg.data.point)

    def test_default_origin(self):
        origin = [0.5, -0.5, 0]
        flatness = 2
        edg = factory.create(
            self.vertex_1, self.vertex_2,
            edges.Origin(origin, flatness)
        )

        self.assertIsInstance(edg, OriginEdge)
        np.testing.assert_array_almost_equal(origin, edg.data.origin)
        self.assertEqual(flatness, edg.data.flatness)

    def test_flat_origin(self):
        origin = [0.5, -0.5, 0]
        edg = factory.create(self.vertex_1, self.vertex_2, edges.Origin(origin))

        self.assertIsInstance(edg, OriginEdge)
        np.testing.assert_array_almost_equal(origin, edg.data.origin)
        self.assertEqual(1, edg.data.flatness)

    def test_angle(self):
        angle = np.pi/6
        axis = [0., 0., 1.]
        edge = factory.create(self.vertex_1, self.vertex_2,
                              edges.Angle(angle, axis))

        self.assertIsInstance(edge, AngleEdge)
        self.assertEqual(angle, edge.data.angle)
        np.testing.assert_array_equal(axis, edge.data.axis)

    def test_spline(self):
        points = [[0.3, 0.25, 0], [0.6, 0.1, 0], [0.3, 0.25, 0]]
        edg = factory.create(self.vertex_1, self.vertex_2,
            edges.Spline(points))

        self.assertIsInstance(edg, SplineEdge)
        np.testing.assert_array_equal(points, edg.data.points)

    def test_polyline(self):
        points = [[0.3, 0.25, 0], [0.6, 0.1, 0], [0.3, 0.25, 0]]
        edg = factory.create(self.vertex_1, self.vertex_2,
            edges.PolyLine(points))

        self.assertIsInstance(edg, SplineEdge)
        np.testing.assert_array_equal(points, edg.data.points)

    def test_project_edge_single(self):
        geometry = 'terrain'
        edg = factory.create(
            self.vertex_1, self.vertex_2,
            edges.Project(geometry))

        self.assertIsInstance(edg, ProjectEdge)
        self.assertListEqual(edg.data.geometry, [geometry])
    
    def test_project_edge_multi(self):
        geometry = ['terrain', 'walls']
        edg = factory.create(
            self.vertex_1, self.vertex_2,
            edges.Project(geometry))

        self.assertIsInstance(edg, ProjectEdge)
        self.assertListEqual(edg.data.geometry, geometry)
    
class EdgeValidityTests(unittest.TestCase):
    """Exclusive tests of Edge.is_valid property"""
    def get_edge(self, data:edges.EdgeData) -> Edge:
        """A shortcut to factory method"""
        return factory.create(
            Vertex([0, 0, 0], 0), Vertex([1, 0, 0], 1), data
        )
    
    def test_degenerate(self):
        """An edge between two vertices at the same point"""
        edge = factory.create(Vertex([0, 0, 0], 0), Vertex([1, 0, 0], 1), edges.Line())
        self.assertFalse(edge.is_valid)

    def test_line_edge(self):
        """line.is_valid"""
        # always false because lines need not be included in blockMeshDict, thus
        # they must be dropped
        self.assertFalse(self.get_edge(edges.Line()).is_valid)

    def test_valid_arc(self):
        """arc.is_valid"""
        self.assertTrue(self.get_edge(edges.Arc([0.5, 0.2, 0])).is_valid)

    def test_invalid_arc(self):
        """Arc from three collinear points"""
        self.assertFalse(self.get_edge(edges.Arc([0.5, 0, 0])).is_valid)
    
    def test_invalid_origin(self):
        """Catch exceptions raised when calculating arc point from the 'origin' alternative"""
        with self.assertRaises(ValueError):
            edge = self.get_edge(edges.Origin([0.5, 0, 0]))
            _ = edge.is_valid
    
    def test_valid_origin(self):
        """A normal arc edge"""
        self.assertTrue(self.get_edge(edges.Arc([0.5, 0.1, 0])).is_valid)
    
    def test_invalid_angle(self):
        """Catch exceptions raised whtn calculating arc point from the 'angle' alternative"""
        with self.assertRaises(AssertionError):
            edge = self.get_edge(edges.Angle(0, [0, 0, 1]))
            _ = edge.is_valid
        
    def test_valid_angle(self):
        """A normal angle edge"""
        self.assertTrue(self.get_edge(edges.Angle(np.pi, [0, 0, 1])).is_valid)

    def test_valid_spline(self):
        """Spline edges are always valid"""
        self.assertTrue(self.get_edge(edges.Spline([[0, 0, 0], [0, 0, 0], [0, 0, 0]])).is_valid)
    
    def test_valid_polyline(self):
        """Same as spline, always valid"""
        self.assertTrue(self.get_edge(edges.PolyLine([[0, 0, 0], [0, 0, 0], [0, 0, 0]])).is_valid)

    def test_valid_project(self):
        """Projected edges cannot be checked for validity, therefore... they are assumed valid"""
        self.assertTrue(self.get_edge(edges.Project(['terrain', 'walls'])).is_valid)

class EdgeLengthTests(unittest.TestCase):
    """Various edge's lengths"""
    def get_edge(self, data:edges.EdgeData) -> Edge:
        """A shortcut to factory method"""
        return factory.create(
            Vertex([0, 0, 0], 0), Vertex([1, 0, 0], 1), data
        )

    def test_arc_edge(self):
        """Length of a classical arc edge"""
        self.assertAlmostEqual(
            self.get_edge(edges.Arc([0.5, 0.5, 0])).length,
            0.5*np.pi
        )

    def test_origin_edge(self):
        """Length of the 'origin' edge"""
        self.assertAlmostEqual(
            self.get_edge(edges.Origin([0.5, -0.5, 0])).length,
            2**0.5*np.pi/4
        )
        
    def test_spline_edge(self):
        """Length of the 'spline' edge - the segments, actually"""
        self.assertEqual(self.get_edge(edges.Spline([[1, 0, 0], [1, 1, 0]])).length, 3)

    def test_project_edge(self):
        """Length of the 'project' edge is equal to a line"""
        self.assertEqual(self.get_edge(edges.Project('terrain')).length, 1)
    
    def test_flattened_edge(self):
        """A 'flattened' origin edge is shorter"""
        self.assertLess(
            self.get_edge(edges.Origin([0.5, -0.5, 0], 2)).length,
            self.get_edge(edges.Origin([0.5, -0.5, 0], 1)).length
        )

class AlternativeArcTests(unittest.TestCase):
    """Origin and Axis arc specification"""
    unit_sq_corner = f.vector(2**0.5/2, 2**0.5/2, 0)

    def test_arc_mid(self):
        axis = f.vector(0, 0, 1)
        center = f.vector(0, 0, 0)
        radius = 1
        edge_point_1 = f.vector(1, 0, 0)
        edge_point_2 = f.vector(0, 1, 0)

        np.testing.assert_array_almost_equal(
            f.arc_mid(axis, center, radius, edge_point_1, edge_point_2),
            self.unit_sq_corner
        )

    def test_arc_from_theta(self):
        edge_point_1 = f.vector(0, 1, 0)
        edge_point_2 = f.vector(1, 0, 0)
        angle = np.pi/2
        axis = f.vector(0, 0, -1)

        np.testing.assert_array_almost_equal(
            arc_from_theta(edge_point_1, edge_point_2, angle, axis),
            self.unit_sq_corner
        )

    def test_arc_from_origin(self):
        edge_point_1 = f.vector(0, 1, 0)
        edge_point_2 = f.vector(1, 0, 0)
        center = f.vector(0, 0, 0)

        np.testing.assert_array_almost_equal(
            arc_from_origin(edge_point_1, edge_point_2, center),
            self.unit_sq_corner
        )

    def test_arc_from_origin_warn(self):
        edge_point_1 = f.vector(0, 1, 0)
        edge_point_2 = f.vector(1.1, 0, 0)
        center = f.vector(0, 0, 0)

        with self.assertWarns(Warning):
            adjusted_point = arc_from_origin(edge_point_1, edge_point_2, center)
        
        expected_point = f.vector(0.75743894, 0.72818283, 0)
        
        np.testing.assert_array_almost_equal(
            adjusted_point,
            expected_point
        )

class EdgeDescriptionTests(unittest.TestCase):
    """Tests of edge outputs"""
    def get_edge(self, data:edges.EdgeData) -> Edge:
        """A shortcut to factory method"""
        return factory.create(
            Vertex([0, 0, 0], 0), Vertex([1, 0, 0], 1), data
        )

    def test_arc_description(self):
        self.assertEqual(
            self.get_edge(edges.Arc([0.5, 0.1, 0])).description,
            "\tarc 0 1 (0.50000000 0.10000000 0.00000000)"
        )
    
    def test_angle_description(self):
        self.assertEqual(
            self.get_edge(edges.Angle(np.pi, [0, 0, 1])).description,
            f"\t// arc 0 1 {np.pi} (0.00000000 0.00000000 1.00000000)\n" + \
            "\tarc 0 1 (0.50000000 -0.50000000 0.00000000)"
        )

    def test_origin_description(self):
        self.assertEqual(
            self.get_edge(edges.Origin([0.5, -0.5, 0])).description,
            "\t// arc 0 1 origin 1 (0.50000000 -0.50000000 0.00000000)\n" + \
            "\tarc 0 1 (0.50000000 0.20710678 0.00000000)"
        )

    def test_spline_description(self):
        self.assertEqual(
            self.get_edge(edges.Spline([[0, 1, 0], [1, 1, 0]])).description,
            "\tspline 0 1 ((0.00000000 1.00000000 0.00000000) (1.00000000 1.00000000 0.00000000))"
        )
