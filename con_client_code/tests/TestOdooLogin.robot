*** Settings ***
Documentation		Example using SeleniumLibrary
Library			Selenium2Library

*** Variables ***
${LOGIN URL}		http://localhost:30000/web/login
${BROWSER}		Chrome

*** Test Cases ***
Valid Login
	Open Browser To Login Page
	Input Username	admin
	Input Password	123456
	Submit Credencials
	Welcome Page Should Be Open
	Go to Sales Module
	Go to Customers
	

*** Keywords ***
Open Browser To Login Page
	Open Browser		${LOGIN URL}	${BROWSER}
	Title Should Be		Login | My Website

Input Username
	[Arguments]	${login}
	Input Text	login	${login}

Input Password
	[Arguments]	${password}
	Input Text	password	${password}

Submit Credencials
	Press Key	id=password	\\13

Welcome Page Should Be Open
	Title Should Be		Odoo

Go to Sales Module
    Wait Until Page Contains Element	xpath=//body[contains(@class, 'o_application_switcher')]
    Click Element      xpath=//div[@class="o_application_switcher_scrollable"]/div[@class="o_apps"]/a[@data-menu-xmlid="sale.sale_menu_root"]
    Title Should Be     Cotizaciones - Odoo

Go to Customers
    Click Element       xpath=//a[@data-menu-xmlid="sale.sale_order_menu"]
    Click Element       xpath=//a[@data-menu-xmlid="sale.res_partner_menu"]
    Title Should Be     Cliente - Odoo