func_module_test_double_examples = """
# Testing with Function Module Test Doubles

This example demonstrates how to use a test double framework for function modules in ABAP unit tests.  Using test doubles allows us to isolate our code under test (CUT) from external dependencies, such as function modules, making tests more reliable and easier to manage.

## Code Under Test (CUT)

Consider the following class `cl_ftd_expense_manager`, which calculates the total expenses after converting currencies using the function module `FTD_CONVERT_CURRENCY`:

class cl_ftd_expense_manager implementation.

  method calculate_total_expense.
    data lv_converted_amount type i.

    loop at lt_expenses into data(ls_expense).

      clear lv_converted_amount.

      " Function module dependency
      call function 'FTD_CONVERT_CURRENCY'
        exporting
          amount             = ls_expense-amount
          source_currency    = ls_expense-currency_code
          target_currency    = lv_currency_code
        importing
          target_curr_amount = lv_converted_amount
        exceptions
          no_rate_found      = 1
          conversion_error   = 2
          others             = 3.
      if sy-subrc <> 0.
        raise exception new cx_ftd_currency_conv_error( ).
      endif.

      lv_result = lv_result + lv_converted_amount.

    endloop.
  endmethod.

endclass.

Explanation:
The method calculate_total_expense iterates through a list of expenses, converts each amount to the target currency using the FTD_CONVERT_CURRENCY function module, and accumulates the converted amounts.

Setting up the Test Environment and Test Doubles
To test calculate_total_expense, we'll replace the real FTD_CONVERT_CURRENCY with a test double that we can control. This is done in the class_setup method of the test class.

method class_setup.
  " Creates a test environment instance which can be used to get function test doubles.
  " All further CALL FUNCTION statements for 'FTD_CONVERT_CURRENCY' will be redirected to the test double.
  go_fm_test_double = cl_function_test_environment=>create( value #( ( 'FTD_CONVERT_CURRENCY' ) ) ).
endmethod.

Explanation:
cl_function_test_environment=>create creates an instance of the test environment and registers FTD_CONVERT_CURRENCY as a function module that needs to be replaced by a test double.
go_fm_test_double is an instance variable, holding the test environment and allowing access to the function module test doubles.

Configuring Test Doubles
We configure the test double to behave according to the needs of our tests. We can specify which output it should return for given inputs.

method test_calculate_total_expense.
    " Get the test double for 'FTD_CONVERT_CURRENCY' from the test environment
    data(go_currency_converter) = go_fm_test_double->get_double( 'FTD_CONVERT_CURRENCY' ).

    " Define input and output configurations

    " Input Config amount = 100, USD to EUR
    data(go_conv_curr_input_config_1) = go_currency_converter->create_input_configuration( )->set_importing_parameter( name = 'AMOUNT' value = 100
                                                                                     )->set_importing_parameter( name = 'SOURCE_CURRENCY' value = 'USD'
                                                                                     )->set_importing_parameter( name = 'TARGET_CURRENCY' value = 'EUR' ).

    " Output Config 1: return 80 (converted amount)
    data(go_conv_curr_output_config_1) = go_currency_converter->create_output_configuration( )->set_exporting_parameter( name = 'TARGET_CURR_AMOUNT' value = 80 ).

    " Configure test double: When the input matches Config 1, return output Config 1
    go_currency_converter->configure_call( )->when( go_conv_curr_input_config_1 )->then_set_output( go_conv_curr_output_config_1 ).

     " Input Config 2: amount = 200, USD to EUR
    data(go_conv_curr_input_config_2) = go_currency_converter->create_input_configuration( )->set_importing_parameter( name = 'AMOUNT' value = 200
                                                                                     )->set_importing_parameter( name = 'SOURCE_CURRENCY' value = 'USD'
                                                                                     )->set_importing_parameter( name = 'TARGET_CURRENCY' value = 'EUR' ).
    " Output Config 2: return 160
    data(go_conv_curr_output_config_2) = go_currency_converter->create_output_configuration( )->set_exporting_parameter( name = 'TARGET_CURR_AMOUNT' value = 160 ).

    " Configure test double for Input config 2
    go_currency_converter->configure_call( )->when( go_conv_curr_input_config_2 )->then_set_output( go_conv_curr_output_config_2 ).

    " Call the method under test.
    " (Assume lt_expenses contains at least one entry with amount 100 and one with amount 200, currency code 'USD' and the target currency code is 'EUR' for this test case)
    " ... (setup expenses here)
    "lo_expense_manager->calculate_total_expense(  ).
    " ... (assert the result here)

  endmethod.

Explanation:
go_fm_test_double->get_double('FTD_CONVERT_CURRENCY') retrieves the test double instance for the function module.

create_input_configuration and create_output_configuration create configurations for the test double.

set_importing_parameter and set_exporting_parameter specify the input and expected output values.

configure_call( )->when(...)->then_set_output(...) configures the test double to return the specified output when called with matching input.

Verifying Test Double Interactions
After running the code under test, we can verify that the test double was called as expected. This helps ensure that our CUT interacted correctly with its dependencies.

method test_calculate_total_expense.
   " ... (same steps as in the above section to configure test double)
   " ... (execute the code under test)

    " Verify that the function double is called twice
    go_currency_converter->verify( )->is_called_times( 2 ).

    " Verify that the function double is called with the given input config
    go_currency_converter->verify( go_conv_curr_input_config_1 )->is_called_once( ).

    " Verify that the function double is called with the given input config 2
    go_currency_converter->verify( go_conv_curr_input_config_2 )->is_called_once( ).
 endmethod.

Explanation:
verify()->is_called_times(2) asserts that the test double was called two times (total) regardless of input parameters.

verify(go_conv_curr_input_config_1)->is_called_once() asserts that the test double was called exactly once with the input parameters specified in go_conv_curr_input_config_1.

"""
