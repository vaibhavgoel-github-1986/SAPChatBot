oo_abap_test_double_examples="""
ABAP Unit supports object-oriented test doubles to replace depended-on components (DOCs) in unit tests. 
This allows testing the object under test (OUT) in isolation without external dependencies.

Approach for Object-Oriented Test Doubles
To use test doubles, the OUT must interact with the DOC via:
An ABAP Interface
A Non-Final ABAP Class (Subclassing Approach)

Note:
Not all methods of the DOC interface need to be implemented. Use PARTIALLY IMPLEMENTED and define only the required methods.
Private methods cannot be replaced in test-specific subclasses.

Test Double with DOC Interface
 - If the OUT interacts with the DOC via an ABAP interface, create a test double by implementing the interface. Like below:
Class Under Test:
CLASS zcl_jira_issues DEFINITION PUBLIC CREATE PUBLIC.

  PUBLIC SECTION.
    INTERFACES: zif_jira_issues.  " Implements interface for JIRA issues operations

    " Dependencies injected via constructor (HTTP client and utility helper)
    DATA: go_jira_http_client TYPE REF TO zif_jira_http_client,
          go_jira_utility     TYPE REF TO zif_jira_utils.

    " Constructor to allow dependency injection (default to standard implementations)
    METHODS: constructor IMPORTING
                io_http_client  TYPE REF TO zif_jira_http_client OPTIONAL
                io_jira_utility TYPE REF TO zif_jira_utils OPTIONAL.

ENDCLASS.

CLASS zcl_jira_issues IMPLEMENTATION.

  " Constructor - Initializes dependencies (either injected or default implementations)
  METHOD constructor.
    go_jira_http_client = COND #( WHEN io_http_client IS INITIAL THEN NEW zcl_jira_http_client( ) ELSE io_http_client ).
    go_jira_utility     = COND #( WHEN io_jira_utility IS INITIAL THEN NEW zcl_jira_utility( ) ELSE io_jira_utility ).
  ENDMETHOD.

  " Searches for JIRA issues using JQL query parameters
  METHOD zif_jira_issues~search_issue_by_jql.
    CLEAR es_response.

    TRY.
      " Make API call to search for issues
      go_jira_http_client->call_api(
        EXPORTING
          iv_operation    = zif_jira_issues=>gc_search_by_sql
          iv_query_params = go_jira_utility->construct_query_string( is_query_params )
          iv_method       = if_http_entity=>co_request_method_get
        RECEIVING
          rv_json_response = DATA(lv_json_response) ).

    " Catch any JIRA-related exceptions
    CATCH zcx_jira_exceptions INTO DATA(lo_exception).
      RAISE EXCEPTION lo_exception.
    ENDTRY.

    " Deserialize JSON response if available
    IF lv_json_response IS NOT INITIAL.
      /ui2/cl_json=>deserialize( EXPORTING json = lv_json_response CHANGING data = es_response ).
    ENDIF.
  ENDMETHOD.

  " Creates a JIRA issue by sending a POST request
  METHOD zif_jira_issues~create_issue.
    CLEAR es_response.

    " Define mappings for custom fields in JSON request
    DATA(lt_mappings) = VALUE /ui2/cl_json=>name_mappings( 
        ( abap = 'CUSTOMFIELD_10043' json = 'customfield_10043' )
        ( abap = 'CUSTOMFIELD_10035' json = 'customfield_10035' )).

    " Serialize request data into JSON format
    DATA(lv_body) = /ui2/cl_json=>serialize(
                      EXPORTING data = is_request compress = abap_true name_mappings = lt_mappings ).

    TRY.
      " Make API call to create the issue
      go_jira_http_client->call_api(
        EXPORTING
          iv_operation    = zif_jira_issues=>gc_post_issue
          iv_method       = if_http_entity=>co_request_method_post
          iv_cdata        = lv_body
        RECEIVING
          rv_json_response = DATA(lv_json_response) ).

    " Catch any JIRA-related exceptions
    CATCH zcx_jira_exceptions INTO DATA(lo_exception).
      RAISE EXCEPTION lo_exception.
    ENDTRY.

    " Deserialize JSON response into structure
    /ui2/cl_json=>deserialize( EXPORTING json = lv_json_response CHANGING data = es_response ).
  ENDMETHOD.

ENDCLASS.

Expected Test Class:
CLASS ltcl_jira_issues DEFINITION FOR TESTING DURATION SHORT RISK LEVEL HARMLESS.

  PRIVATE SECTION.
    " Dependencies & mock objects
    DATA: go_cut              TYPE REF TO zcl_jira_issues,        " Class Under Test
          go_mock_http_client TYPE REF TO zif_jira_http_client,   " Mock HTTP Client
          go_mock_utility     TYPE REF TO zif_jira_utils.         " Mock Utility

    " Setup & teardown methods for test lifecycle
    METHODS: setup, teardown, create_test_doubles.

    " Unit test methods
    METHODS:
      test_create_issue FOR TESTING,             " Tests issue creation
      test_create_issue_exception FOR TESTING,   " Tests exception handling in create issue
      test_search_issue_by_jql FOR TESTING,      " Tests searching for issues using JQL
      test_search_issue_exception FOR TESTING.   " Tests exception handling in JQL search

ENDCLASS.

CLASS ltcl_jira_issues IMPLEMENTATION.

  " Setup method - Initializes dependencies before each test
  METHOD setup.
    create_test_doubles( ). " Create test doubles for HTTP client and utilities
    go_cut = NEW zcl_jira_issues( io_http_client = go_mock_http_client io_jira_utility = go_mock_utility ).
  ENDMETHOD.

  " Teardown method - Clears dependencies after each test
  METHOD teardown.
    CLEAR: go_cut, go_mock_http_client, go_mock_utility.
  ENDMETHOD.

  " Creates test doubles using ABAP Test Double Framework
  METHOD create_test_doubles.
    go_mock_http_client ?= cl_abap_testdouble=>create( 'ZIF_JIRA_HTTP_CLIENT' ).
    go_mock_utility     ?= cl_abap_testdouble=>create( 'ZIF_JIRA_UTILS' ).
  ENDMETHOD.

  " Test case: Create JIRA issue successfully
  METHOD test_create_issue.
    DATA: ls_request TYPE zif_jira_issues=>ts_create_request,
          ls_response TYPE zif_jira_issues=>ts_create_response.

    " Set up mock request data
    ls_request = VALUE #( fields-summary = 'This is a test issue.' ).

    " Configure mock HTTP client to return JSON response
    cl_abap_testdouble=>configure_call( go_mock_http_client
      )->ignore_all_parameters( )->returning( '{"id":"test_id","key":"test_key"}' ).

    " Call method under test
    go_cut->zif_jira_issues~create_issue( EXPORTING is_request = ls_request IMPORTING es_response = ls_response ).

    " Assert expected key is returned
    cl_abap_unit_assert=>assert_equals( act = ls_response-key exp = 'test_key' msg = 'Unexpected issue key' ).
  ENDMETHOD.

  " Test case: Exception handling during issue creation
  METHOD test_create_issue_exception.
    DATA ls_request TYPE zif_jira_issues=>ts_create_request.
    ls_request = VALUE #( fields-summary = 'This is a test issue.' ).

    " Simulate an exception response
    DATA(lo_exp_exception) = NEW zcx_jira_exceptions( code = 500 reason = 'Test Reason' ).

    " Configure mock HTTP client to raise an exception
    cl_abap_testdouble=>configure_call( go_mock_http_client
      )->ignore_all_parameters( )->raise_exception( lo_exp_exception ).

    " Verify exception is correctly raised
    TRY.
      go_cut->zif_jira_issues~create_issue( EXPORTING is_request = ls_request IMPORTING es_response = DATA(ls_response) ).
      cl_abap_unit_assert=>fail( msg = 'Exception expected but not raised' ).
    CATCH zcx_jira_exceptions INTO DATA(lo_exception).
      cl_abap_unit_assert=>assert_equals( act = lo_exception exp = lo_exp_exception msg = 'Incorrect exception raised' ).
    ENDTRY.
  ENDMETHOD.

  " Test case: Searching JIRA issues using JQL
  METHOD test_search_issue_by_jql.
    DATA: ls_query_params TYPE zif_jira_issues=>ts_query_params,
          ls_response TYPE zif_jira_issues=>ts_search_response.

    " Set mock query parameters
    ls_query_params = VALUE #( jql = 'project = TEST AND status = Open' ).

    " Configure mock HTTP client to return JSON response
    cl_abap_testdouble=>configure_call( go_mock_http_client
      )->ignore_all_parameters( )->returning( '{"issues": [{"key": "test_key"}]}' ).

    " Execute method and assert expected results
    go_cut->zif_jira_issues~search_issue_by_jql( EXPORTING is_query_params = ls_query_params IMPORTING es_response = ls_response ).

    cl_abap_unit_assert=>assert_equals( act = ls_response-issues[ 1 ]-key exp = 'test_key' msg = 'Unexpected issue key' ).
  ENDMETHOD.

ENDCLASS.

**Test Double without DOC Interface (Subclassing)**
📌 If the OUT interacts directly with the DOC, and the DOC is a non-final ABAP class, a test-specific subclass can be created.

Example: Subclassing
CLASS zcl_payment_processor DEFINITION.
  PUBLIC SECTION.
    METHODS process_payment IMPORTING iv_amount TYPE p DECIMALS 2
                            RETURNING VALUE(rv_status) TYPE char1.
ENDCLASS.

CLASS zcl_test_payment_processor DEFINITION INHERITING FROM zcl_payment_processor.
  PUBLIC SECTION.
    METHODS process_payment REDEFINITION.
ENDCLASS.

CLASS zcl_test_payment_processor IMPLEMENTATION.
  METHOD process_payment.
    rv_status = 'X'. "Mocked behavior
  ENDMETHOD.
ENDCLASS.

Note:
Only public and protected methods can be overridden.
Private methods cannot be replaced with this approach.

**Replacing the DOC in the Object Under Test**
There are multiple dependency injection techniques:
Injection Type	Description
Public Injection	Replace the dependency via a public method.
Constructor Injection	Pass the test double in the constructor.
Setter Injection	Provide the test double via a setter method.
Parameter Injection	Pass the test double directly as a parameter to the method.
Private Injection	Overwrite the private dependency in the OUT.
Test Class as Friend	Use FRIENDS to overwrite private attributes.
ABAP Test Seams	Modify the DOC creation logic to instantiate the test double.

Framework Restrictions (Not Supported):
🚫 Local interfaces and local classes
🚫 Classic exceptions
🚫 FINAL or FOR TESTING classes
🚫 PRIVATE constructor classes
🚫 Methods marked as FINAL, STATIC, or PRIVATE

"""
