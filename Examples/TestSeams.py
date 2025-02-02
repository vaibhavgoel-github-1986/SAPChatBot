test_seams_examples = """

Test seams are language constructs designed especially for unit tests and are implemented using the following statements:

TEST-SEAM - END-TEST-SEAM
Defines a test seam as a replaceable area in the production code of a program.

TEST-INJECTION - END-TEST-INJECTION
Replaces the executable statements of a test seam with the statements of an injection in a test class of the same program.

Test seams have the following properties:

Test seams do not affect the use of programs in production. No injection takes place, rather the original code is executed.
A program can contain multiple test seams.
Multiple injections can be defined for a single test seam.
Injections can only be created in test classes that are defined in a test include. Test seams can be used in all executable units of a master program that includes a test include, including methods of local classes and subroutines.
Unit tests can make injections while test methods or the setup method are being executed.
If injections are repeated in the same test seam, the last injection is performed as an active injection.
Hints

Test seams are a simple way of replacing or expanding source code in the production parts of a program for test purposes. If, for example, the behavior of certain statements prevents tests from running, the unit test can replace them with suitable alternatives. Typical scenarios are:
Authorization checks
Reading persistent data
Modifying persistent data
Creating test doubles
Test seams are intended mainly for use with legacy code that, due to insufficient separation of concerns, is not suitable for unit tests. New programs, on the other hand, should be modularized in such a way that test seams are made unnecessary.


Example - Authorization Checks

An injection can replace the statement AUTHORITY-CHECK to bypass the dependency of a unit test on the authorizations of the current user by setting a suitable return code.

Test Seam	Injection
TEST-SEAM authorization_seam.
  AUTHORITY-CHECK OBJECT 'S_CTS_ADMI'
     ID 'CTS_ADMFCT' FIELD 'TABL'.
END-TEST-SEAM.

IF sy-subrc = 0.
  is_authorized = abap_true.
ENDIF.	TEST-INJECTION authorization_seam.
  sy-subrc = 0.
END-TEST-INJECTION.

Example - Reading Persistent Data

It is often not possible to make assumptions about the content of database tables or other repositories in unit tests. Test seams enable unit tests to bypass the dependencies of persistent data by replacing it with self-constructed data.

Test Seam	Injection
TEST-SEAM read_content_seam.
  SELECT *
         FROM sflight
         WHERE  carrid IN @carrid_range AND
fldate EQ @sy-datum
     INTO TABLE @flights.
END-TEST-SEAM.	TEST-INJECTION read_content_seam.
  flights =
    VALUE #( ( carrid = 'LHA'
               connid = 100 )
( carrid = 'AFR'
               connid = 900 ) ).
END-TEST-INJECTION.

Example - Changing Persistent Data

The execution of unit tests must not modify content of database tables or other repositories used in production. Using test seams, unit tests can record the operands of modifying database operations or compare them with expected changes instead of actual changes. In the following source code section compares, the injection compares the change values with a public static attribute.

Test Seam	Injection
TEST-SEAM store_content_seam.
  MODIFY sflight
    FROM TABLE @new_flights.
END-TEST-SEAM.	TEST-INJECTION store_content_seam.
  cl_abap_unit_assert=>assert_equals(
act = new_flights
    exp = global_buffer=>exp_flights ).
END-TEST-INJECTION.

Example - Test Double

In the following source code section, the production source code of a class that depends on database content is instantiated. The unit test injects the instantiated test double instead of the production object.

Test Seam	Injection
TEST-SEAM instantiation_seam.
  me->oref = NEW #( ).
END-TEST-SEAM.	TEST-INJECTION instantiation_seam.
me->oref = NEW dummy_class( ).
END-TEST-INJECTION.

Remember the Restrictions:
Test injections can only refer to test seams located in the same function pool.

You cannot use test seams in reports.

Code completion in test injections is available to a limited extent.

"""
