# pylint: disable-msg=C0111,C0103

import unittest

from openmdao.main.api import Assembly, Driver, set_as_top
from openmdao.util.decorators import add_delegate
from openmdao.main.hasconstraints import HasConstraints, HasEqConstraints, HasIneqConstraints, Constraint
from openmdao.test.execcomp import ExecComp

@add_delegate(HasConstraints)
class MyDriver(Driver):
    pass

@add_delegate(HasEqConstraints)
class MyEqDriver(Driver):
    pass

@add_delegate(HasIneqConstraints)
class MyInEqDriver(Driver):
    pass

class HasConstraintsTestCase(unittest.TestCase):

    def setUp(self):
        self.asm = set_as_top(Assembly())
        self.asm.add('comp1', ExecComp(exprs=['c=a+b', 'd=a-b']))
        
    def test_list_constraints(self):
        drv = self.asm.add('driver', MyDriver())
        drv.add_constraint('comp1.a < comp1.b')
        drv.add_constraint('comp1.c = comp1.d')
        self.assertEqual(drv.list_constraints(), ['comp1.a<comp1.b','comp1.c=comp1.d'])
        
    def test_list_eq_constraints(self):
        drv = self.asm.add('driver', MyEqDriver())
        drv.add_constraint('comp1.a = comp1.b')
        drv.add_constraint('comp1.c = comp1.d')
        self.assertEqual(drv.list_constraints(), ['comp1.a=comp1.b','comp1.c=comp1.d'])
        
    def test_list_ineq_constraints(self):
        drv = self.asm.add('driver', MyDriver())
        drv.add_constraint('comp1.a < comp1.b')
        drv.add_constraint('comp1.c >= comp1.d')
        self.assertEqual(drv.list_constraints(), ['comp1.a<comp1.b','comp1.c>=comp1.d'])
        
    def _check_add_constraint(self, drv, eq=False, ineq=False):
        self.asm.add('driver', drv)

        if eq: 
            self.assertEqual(len(drv.get_eq_constraints()), 0)
        if ineq: 
            self.assertEqual(len(drv.get_ineq_constraints()), 0)
            drv.add_constraint(' comp1.a > comp1.b')
            
        if eq: 
            self.assertEqual(len(drv.get_eq_constraints()), 0)
        if ineq: 
            self.assertEqual(len(drv.get_ineq_constraints()), 1)
        
        if eq: 
            drv.add_constraint('comp1.c =      comp1.d ')
            self.assertEqual(len(drv.get_eq_constraints()), 1)
        if ineq: 
            self.assertEqual(len(drv.get_ineq_constraints()), 1)
        
        if eq: 
            drv.remove_constraint(' comp1.c=comp1.d')
            self.assertEqual(len(drv.get_eq_constraints()), 0)
            try:
                drv.remove_constraint('comp1.bogus = comp1.d')
            except Exception as err:
                self.assertEqual(str(err), 
                    "driver: Constraint 'comp1.bogus = comp1.d' was not found. Remove failed.")
            else:
                self.fail("Exception expected")
        if ineq: 
            self.assertEqual(len(drv.get_ineq_constraints()), 1)
            drv.remove_constraint(' comp1.a>  comp1.b  ')
            self.assertEqual(len(drv.get_ineq_constraints()), 0)
            try:
                drv.remove_constraint('comp1.bogus < comp1.d')
            except Exception as err:
                self.assertEqual(str(err), 
                    "driver: Constraint 'comp1.bogus < comp1.d' was not found. Remove failed.")
            else:
                self.fail("Exception expected")
        if eq: 
            self.assertEqual(len(drv.get_eq_constraints()), 0)
        
        if ineq: 
            drv.add_constraint(' comp1.a > comp1.b')
            self.assertEqual(len(drv.get_ineq_constraints()), 1)
        if eq: 
            drv.add_constraint('comp1.c =comp1.d ')
            self.assertEqual(len(drv.get_eq_constraints()), 1)
        
        drv.clear_constraints()
        if eq: 
            self.assertEqual(len(drv.get_eq_constraints()), 0)
        if ineq: 
            self.assertEqual(len(drv.get_ineq_constraints()), 0)
        
        if ineq:
            try:
                drv.add_constraint('comp1.b < comp1.qq')
            except ValueError as err:
                self.assertEqual(str(err), 
                    "Constraint 'comp1.b < comp1.qq' has an invalid right-hand-side.")
            else:
                self.fail('expected ValueError')
        else:
            try:
                drv.add_constraint('comp1.qq = comp1.b')
            except ValueError as err:
                self.assertEqual(str(err), 
                   "Constraint 'comp1.qq = comp1.b' has an invalid left-hand-side.")
            else:
                self.fail('expected ValueError')
        
    def _check_eval_constraints(self, drv, eq=False, ineq=False):
        self.asm.add('driver', drv)
        
        if eq: 
            vals = drv.eval_eq_constraints()
            self.assertEqual(len(vals), 0)
        
        if ineq: 
            vals = drv.eval_ineq_constraints()
            self.assertEqual(len(vals), 0)
        
        if ineq: 
            drv.add_constraint(' comp1.a > comp1.b')
        if eq: 
            drv.add_constraint('comp1.c = comp1.d ')
        
        self.asm.comp1.a = 4
        self.asm.comp1.b = 5
        self.asm.comp1.c = 9
        self.asm.comp1.d = 9
        
        if eq:
            vals = drv.eval_eq_constraints()
            self.assertEqual(len(vals), 1)
            self.assertEqual(vals[0][0], 9)
            self.assertEqual(vals[0][1], 9)
            self.assertEqual(vals[0][2], '=')
            self.assertEqual(vals[0][3], False)
            
            vals = drv.get_eq_constraints()
            self.assertEqual(len(vals), 1)
            self.assertTrue(isinstance(vals['comp1.c=comp1.d'], Constraint))

        if ineq:
            vals = drv.eval_ineq_constraints()
            self.assertEqual(len(vals), 1)
            self.assertEqual(vals[0][0], 4)
            self.assertEqual(vals[0][1], 5)
            self.assertEqual(vals[0][2], '>')
            self.assertEqual(vals[0][3], True)

            vals = drv.get_ineq_constraints()
            self.assertEqual(len(vals), 1)
            self.assertTrue(isinstance(vals['comp1.a>comp1.b'], Constraint))

    def test_constraint_scaler_adder(self):
        drv = self.asm.add('driver', MyDriver())
        self.asm.comp1.a = 3000
        self.asm.comp1.b = 5000
        drv.add_constraint('comp1.a < comp1.b', scaler=1.0/1000.0, adder=-4000.0)
        result = drv.eval_ineq_constraints()
        
        self.assertEqual(result[0][0], -1.0)
        self.assertEqual(result[0][1], 1.0)
        
        try:
            drv.add_constraint('comp1.a < comp1.b', scaler=-5.0)
        except ValueError as err:
            self.assertEqual(str(err), 
               "Scaler parameter should be a float > 0")
        else:
            self.fail('expected ValueError')
            
        try:
            drv.add_constraint('comp1.a < comp1.b', scaler=2)
        except ValueError as err:
            self.assertEqual(str(err), 
               "Scaler parameter should be a float")
        else:
            self.fail('expected ValueError')
    
        try:
            drv.add_constraint('comp1.a < comp1.b', adder=2)
        except ValueError as err:
            self.assertEqual(str(err), 
               "Adder parameter should be a float")
        else:
            self.fail('expected ValueError')
    
    def test_add_constraint(self):
        self._check_add_constraint(MyDriver(), eq=True, ineq=True)
    
    def test_add_eq_constraint(self):
        self._check_add_constraint(MyEqDriver(), eq=True)
    
    def test_add_ineq_constraint(self):
        self._check_add_constraint(MyInEqDriver(), ineq=True)
    
    def test_implicit_constraint(self):
        drv = self.asm.add('driver', MyEqDriver())
        try:
            drv.add_constraint('comp1.a + comp1.b')
        except ValueError, err:
            self.assertEqual(str(err),
                             "driver: Constraints require an explicit comparator (=, <, >, <=, or >=)")
        else:
            self.fail('ValueError expected')
            
        
    def test_eval_constraint(self):
        self._check_eval_constraints(MyDriver(), eq=True, ineq=True)

    def test_eval_eq_constraint(self):
        self._check_eval_constraints(MyEqDriver(), eq=True)

    def test_eval_ineq_constraint(self):
        self._check_eval_constraints(MyInEqDriver(), ineq=True)

if __name__ == "__main__":
    unittest.main()

