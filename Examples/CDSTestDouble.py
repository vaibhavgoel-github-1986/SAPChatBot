cds_test_double_examples="""
Writing a Unit Test for a CDS Entity Using the CDS Test Double Framework
Key Concepts
✔ CDS Test Doubles: Generated for first-level dependencies of the CDS entity under test (CUT).
✔ CDS Test Environment: Redirects CDS queries to test doubles, ensuring controlled test scenarios.
✔ Hierarchical Testing: Tests deeper CDS dependencies using selective test doubles.

CDS Code Under Test: CDS View
@AbapCatalog.sqlViewName: 'ZCDS_DEMO_1'
@EndUserText.label: 'Calculations in SELECT list'
@AbapCatalog.compiler.compareFilter: true
define view zcds_Sales_Order_Item
  as select from snwd_so_i
  association [1] to snwd_pd as _product 
  on snwd_so_i.product_guid = _product.node_key
{
  key snwd_so_i.node_key as so_item_guid,
      parent_key as so_guid,
      snwd_so_i.product_guid,
      snwd_so_i.so_item_pos,
      currency_code,
      gross_amount,
      case net_amount
          when 0 then 0
          else cast( ( division( tax_amount, net_amount, 4 ) * 100 ) as abap.dec(15,2) )
      end as tax_rate,
      division( tax_amount, net_amount, 4 ) * 100 as demo,
      _product
}

**Creating a Unit Test Class**
CLASS ltc_cds_sales_order DEFINITION FINAL FOR TESTING 
  DURATION SHORT RISK LEVEL HARMLESS.

  PRIVATE SECTION.
    CLASS-DATA: go_cds_test_double TYPE REF TO if_cds_test_environment.

    METHODS:
      class_setup FOR TESTING CLASS-SETUP,
      setup FOR TESTING SETUP,
      calculate_tax_rate FOR TESTING,
      class_teardown FOR TESTING CLASS-TEARDOWN.

ENDCLASS.

1. Setting Up the CDS Test Double Environment
METHOD class_setup.
 " Test doubles would be created for 'zcds_So_Items_By_TaxRate' and 'snwd_so'.
  go_cds_test_double = cl_cds_test_environment=>create( i_for_entity = 'zcds_Sales_Order_Item' ).
ENDMETHOD.

METHOD setup.
 " Ensures fresh data before each test execution.
  go_cds_test_double->clear_doubles( ).
  
ENDMETHOD.

METHOD class_teardown.
 " Cleans up test doubles and environment after tests are executed.
  go_cds_test_double->destroy( ).  
ENDMETHOD.

2. Writing a Unit Test for CDS View
METHOD calculate_tax_rate.

  " Prepare and insert test data
  DATA(lt_sales_order_items) = VALUE #( ( client = sy-mandt net_amount = 333 tax_amount = 111 ) ).
  go_cds_test_double->insert_test_data( i_data = lt_sales_order_items ).

  " Execute the CDS entity under test
  SELECT * FROM zcds_Sales_Order_Item INTO TABLE @DATA(lt_act_results).

  " Verify the results
  cl_abap_unit_assert=>assert_equals( act = LINES( lt_act_results ) exp = 1 msg = 'Tax Rate not as expected' ).
  cl_abap_unit_assert=>assert_equals( act = lt_act_results[ 1 ]-tax_rate exp = '33.33' msg = 'Tax Rate not as expected').

ENDMETHOD.

3. Unit Testing a CDS View - Modeled Associations
METHOD class_setup.
  go_cds_test_double = cl_cds_test_environment=>create( 
                          i_for_entity = 'zcds_Open_So_Items_By_TaxR'
                          test_associations = 'X' ).
  " Test doubles created for 'zcds_So_Items_By_TaxRate', 'snwd_so', and 'zcds_Modeled_Assoc'.
ENDMETHOD.

4. Hierarchical Testing for CDS Entities
Hierarchy Test - Specify All Dependencies
METHOD class_setup.
  go_cds_test_double = cl_cds_test_environment=>create( 
                          i_for_entity = 'zcds_Open_So_Items_By_TaxR'
                          i_dependency_list = VALUE #( 
                               ( name = 'zcds_Sales_Order_Item' type = 'CDS_VIEW' )
                               ( name = 'SNWD_SO' type = 'TABLE' ) ) ).
  " Test doubles created for 'zcds_Sales_Order_Item', 'snwd_so'.
  " The logic inside 'zcds_Open_So_Items_By_TaxR' and 'zcds_So_Items_By_TaxRate' can be tested.
ENDMETHOD.

Hierarchy Test - Select Leaf Nodes
METHOD class_setup.
  go_cds_test_double = cl_cds_test_environment=>create( 
                          i_for_entity = 'zcds_Open_So_Items_By_TaxR'
                          i_dependency_list = VALUE #( ( name = 'zcds_Sales_Order_Item' type = 'CDS_VIEW' ) )
                          i_select_base_dependencies = abap_true ).
  " Test doubles created for 'zcds_Sales_Order_Item', 'snwd_so'.
ENDMETHOD.

Hierarchy Test - Select All Leaf Nodes
METHOD class_setup.
  go_cds_test_double = cl_cds_test_environment=>create( 
                          i_for_entity = 'zcds_Open_So_Items_By_TaxR'
                          i_select_base_dependencies = abap_true ).
  " Test doubles created for 'snwd_so', 'snwd_so_i'.
ENDMETHOD.

5. Writing Tests for Multiple CDS Entities
METHOD class_setup.
  go_cds_test_double = cl_cds_test_environment=>create_for_multiple_cds(
                          i_for_entities = VALUE #(
                            ( i_for_entity = 'zcds_Open_So_Items_By_TaxR'
                              i_select_base_dependencies = abap_true
                              i_dependency_list = VALUE #( ( 'zcds_Sales_Order_Item' ) ) )
                            ( i_for_entity = 'I_BUSINESSUSER' ) ) ).

  " Hierarchy testing for 'zcds_Open_So_Items_By_TaxR' with dependencies.
  " Test double created for 'zcds_Sales_Order_Item'.
  " Unit testing for 'I_BUSINESSUSER'.
ENDMETHOD.
"""