#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest

from soql.attributes import Integer, Relationship, String
from soql import Model
from soql import select
from soql import SelectClauseIsntValidSubquery
from soql import asc, desc, nulls_first, nulls_last
from tests.helpers import SoqlAssertions


class Grandparent(Model):
    id = Integer('Id')


class Parent(Model):
    id = Integer('Id')
    name = String('Name')
    age = Integer('Age')
    mom = Relationship('Mom', related_model=Grandparent)


class Child(Model):
    id = Integer('Id')
    name = String('Name')
    mom = Relationship('Mom', related_model=Parent)
    dad = Relationship('Dad', related_model=Parent)
    teacher = Relationship('Teacher', related_model='Teacher')


class Teacher(Model):
    id = Integer('Id')
    students = Relationship('Students', related_model=Child, many=True)


class SelectTest(unittest.TestCase, SoqlAssertions):
    def test_select(self):
        self.assertSoqlEqual(
            select(Child),
            "SELECT Child.Id, Child.Name "
            "FROM Child"
        )

    def test_joins(self):
        self.assertSoqlEqual(
            select(Child).join(Child.mom),
            "SELECT Child.Id, Child.Name, Child.Mom.Age, Child.Mom.Id, Child.Mom.Name "
            "FROM Child"
        )

        self.assertSoqlEqual(
            select(Teacher).join(Teacher.students),
            "SELECT Teacher.Id, (SELECT Child.Id, Child.Name FROM Teacher.Students) "
            "FROM Teacher"
        )

        self.assertSoqlEqual(
            select(Teacher).join(Teacher.students).join(Teacher.students.mom),
            "SELECT Teacher.Id, "
            "(SELECT Child.Id, Child.Name, Child.Mom.Age, Child.Mom.Id, Child.Mom.Name FROM Teacher.Students) "
            "FROM Teacher"
        )

        self.assertSoqlEqual(
            select(Teacher).join(Teacher.students.mom),
            "SELECT Teacher.Id, "
            "(SELECT Child.Id, Child.Name, Child.Mom.Age, Child.Mom.Id, Child.Mom.Name FROM Teacher.Students) "
            "FROM Teacher"
        )

        self.assertSoqlEqual(
            select(Child).join(Child.mom.mom),
            "SELECT Child.Id, Child.Name, Child.Mom.Age, "
            "Child.Mom.Id, Child.Mom.Name, Child.Mom.Mom.Id "
            "FROM Child"
        )

        self.assertSoqlEqual(
            select(Teacher).join(Teacher.students.mom).join(
                Teacher.students.dad),
            "SELECT Teacher.Id, "
            "(SELECT Child.Id, Child.Name, Child.Dad.Age, Child.Dad.Id, Child.Dad.Name, "
            "Child.Mom.Age, Child.Mom.Id, Child.Mom.Name FROM Teacher.Students) "
            "FROM Teacher"
        )

        self.assertSoqlEqual(
            select(Child).join(Child.teacher.students.mom),
            "SELECT Child.Id, Child.Name, Child.Teacher.Id, "
            "(SELECT Child.Id, Child.Name, Child.Mom.Age, Child.Mom.Id, "
            "Child.Mom.Name FROM Child.Teacher.Students) "
            "FROM Child"
        )

    def test_filters(self):
        self.assertSoqlEqual(
            select(Child).where(Child.id == '123'),
            "SELECT Child.Id, Child.Name "
            "FROM Child "
            "WHERE Child.Id = '123'"
        )

        self.assertSoqlEqual(
            select(Child).where(Child.id == '123').where(Child.name == 'Jill'),
            "SELECT Child.Id, Child.Name "
            "FROM Child "
            "WHERE Child.Id = '123' AND Child.Name = 'Jill'"
        )

        self.assertSoqlEqual(
            select(Child).where(Child.name == u'CATMONKÈ-123490'),
            u"SELECT Child.Id, Child.Name "
            u"FROM Child "
            u"WHERE Child.Name = 'CATMONKÈ-123490'"
        )

    def test_order_by(self):
        self.assertSoqlEqual(
            select(Parent).order_by(Parent.age),
            "SELECT Parent.Age, Parent.Id, Parent.Name "
            "FROM Parent "
            "ORDER BY Parent.Age"
        )

        self.assertSoqlEqual(
            select(Parent).order_by(Parent.age).order_by(Parent.id),
            "SELECT Parent.Age, Parent.Id, Parent.Name "
            "FROM Parent "
            "ORDER BY Parent.Age, Parent.Id"
        )

        self.assertSoqlEqual(
            select(Parent).order_by(Parent.age, direction=desc),
            "SELECT Parent.Age, Parent.Id, Parent.Name "
            "FROM Parent "
            "ORDER BY Parent.Age DESC"
        )

        self.assertSoqlEqual(
            select(Parent).order_by(Parent.age, direction=desc).order_by(Parent.id, direction=asc),
            "SELECT Parent.Age, Parent.Id, Parent.Name "
            "FROM Parent "
            "ORDER BY Parent.Age DESC, Parent.Id ASC"
        )

        self.assertSoqlEqual(
            select(Parent).order_by(Parent.age, direction=asc, nulls_position=nulls_first),
            "SELECT Parent.Age, Parent.Id, Parent.Name "
            "FROM Parent "
            "ORDER BY Parent.Age ASC NULLS FIRST"
        )

        self.assertSoqlEqual(
            select(Parent).order_by(Parent.age, direction=desc, nulls_position=nulls_last),
            "SELECT Parent.Age, Parent.Id, Parent.Name "
            "FROM Parent "
            "ORDER BY Parent.Age DESC NULLS LAST"
        )

    def test_count(self):
        self.assertSoqlEqual(
            select(Child).count(),
            "SELECT COUNT() "
            "FROM Child"
        )

    def test_offset_and_limit(self):
        self.assertSoqlEqual(
            select(Child).limit(100),
            "SELECT Child.Id, Child.Name "
            "FROM Child "
            "LIMIT 100"
        )

        self.assertSoqlEqual(
            select(Child).offset(100),
            "SELECT Child.Id, Child.Name "
            "FROM Child "
            "OFFSET 100"
        )

        self.assertSoqlEqual(
            select(Parent).order_by(Parent.age).offset(100).limit(100),
            "SELECT Parent.Age, Parent.Id, Parent.Name "
            "FROM Parent "
            "ORDER BY Parent.Age "
            "LIMIT 100 "
            "OFFSET 100"
        )

    def test_override_columns(self):
        self.assertSoqlEqual(
            select(Parent).columns(Parent.id),
            "SELECT Parent.Id "
            "FROM Parent"
        )

        self.assertSoqlEqual(
            select(Parent).columns(Parent.id, Parent.name),
            "SELECT Parent.Id, Parent.Name "
            "FROM Parent"
        )

    def test_subquery(self):
        self.assertSoqlEqual(
            select(Parent).columns(Parent.id).subquery(),
            "(SELECT Parent.Id FROM Parent)"
        )

        subquery = select(Parent).columns(Parent.name).subquery()
        self.assertSoqlEqual(
            select(Child).where(Child.name.in_(subquery)),
            "SELECT Child.Id, Child.Name "
            "FROM Child "
            "WHERE Child.Name IN (SELECT Parent.Name FROM Parent)"
        )

        with self.assertRaises(SelectClauseIsntValidSubquery):
            select(Parent).offset(100).subquery()
