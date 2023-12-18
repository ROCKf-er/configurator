// This file is automatically generated from "./parameters.xml" file by script "parameters_to_header.py".

#ifndef CONSTRAINTS_H
#define CONSTRAINTS_H

#include "main.h"

param_constraint param_costraint_arr[PARAM_COUNT] = {
	{
		-30, // float min_value;
		30, // float max_value;
		1, // float step_value;
		10, // float default_value;
		"Кут крену при пошуку цілі (при RSSI < THRESHOLD)", // char description[300];
		false, // bool actual;
	},
	{
		0.00, // float min_value;
		2.00, // float max_value;
		0.01, // float step_value;
		0.75, // float default_value;
		"Відсоток від ROLL’у на руль повороту", // char description[300];
		false, // bool actual;
	},
	{
		0.20, // float min_value;
		5.00, // float max_value;
		0.01, // float step_value;
		1.00, // float default_value;
		"Пропорційний коефіцієнт", // char description[300];
		false, // bool actual;
	},
	{
		-100.00, // float min_value;
		100.00, // float max_value;
		0.01, // float step_value;
		0.00, // float default_value;
		"Інтегральний коефіцієнт. Відладка", // char description[300];
		false, // bool actual;
	},
	{
		-100.00, // float min_value;
		100.00, // float max_value;
		0.01, // float step_value;
		0.00, // float default_value;
		"Диференціальний коефіцієнт. Відладка", // char description[300];
		false, // bool actual;
	},
	{
		-45, // float min_value;
		45, // float max_value;
		1, // float step_value;
		0, // float default_value;
		"Кут встановлення антенного модуля (-20º – нормаль антени відхилена вниз від осі літака)", // char description[300];
		false, // bool actual;
	},
	{
		1100, // float min_value;
		1900, // float max_value;
		1, // float step_value;
		1900, // float default_value;
		"Сигнал на закриття скиду. Режим БОМБЕР", // char description[300];
		false, // bool actual;
	},
	{
		1100, // float min_value;
		1900, // float max_value;
		1, // float step_value;
		1220, // float default_value;
		"Сигнал на відкриття скиду. Режим БОМБЕР", // char description[300];
		false, // bool actual;
	},
	{
		1, // float min_value;
		8, // float max_value;
		1, // float step_value;
		8, // float default_value;
		"Номер каналу для підключення механізму скидання. Режим БОМБЕР", // char description[300];
		false, // bool actual;
	},
	{
		100, // float min_value;
		400, // float max_value;
		1, // float step_value;
		150, // float default_value;
		"Висота пошуку цілі", // char description[300];
		false, // bool actual;
	},
	{
		0.30, // float min_value;
		100.00, // float max_value;
		0.01, // float step_value;
		20.00, // float default_value;
		"Швидкість м/с при пошуку цілі. При відсутності трубки Піто встановити значення 0..1, що відповідатиме % газу", // char description[300];
		false, // bool actual;
	},
	{
		1, // float min_value;
		360, // float max_value;
		1, // float step_value;
		120, // float default_value;
		"Після ввімкнення режиму Guided пошук цілі буде відбуватися у проміжку від (Heading –  SCAN_SECTOR / 2) до (Heading +  SCAN_SECTOR / 2)", // char description[300];
		false, // bool actual;
	},
	{
		50, // float min_value;
		200, // float max_value;
		1, // float step_value;
		100, // float default_value;
		"Висота заходу на ціль. Режим БОМБЕР", // char description[300];
		false, // bool actual;
	},
	{
		-80, // float min_value;
		-50, // float max_value;
		1, // float step_value;
		-70, // float default_value;
		"Рівень сигналу при якому відбувається зниження до DROP_ALT. Режим БОМБЕР", // char description[300];
		false, // bool actual;
	},
	{
		0.30, // float min_value;
		100.00, // float max_value;
		0.01, // float step_value;
		25.00, // float default_value;
		"Швидкість м/с при заході на ціль. При відсутності трубки Піто встановити значення 0..1, що відповідатиме % газу. Режим БОМБЕР", // char description[300];
		false, // bool actual;
	},
	{
		-90, // float min_value;
		0, // float max_value;
		1, // float step_value;
		-45, // float default_value;
		"Кут на ціль відносно літака, при якому скидається вантаж. Режим БОМБЕР", // char description[300];
		false, // bool actual;
	},
	{
		0, // float min_value;
		2, // float max_value;
		1, // float step_value;
		2, // float default_value;
		"Тип застосування: 0 - БОМБЕР, 1 - БОМБЕР з поверненням додому, 2 - КАМІКАДЗЕ", // char description[300];
		false, // bool actual;
	},
	{
		-60, // float min_value;
		0, // float max_value;
		1, // float step_value;
		-30, // float default_value;
		"Кут пікірування. DIVING_ANGLE - ANTENNA_ANGLE >= -30.  Режим КАМІКАДЗЕ", // char description[300];
		false, // bool actual;
	},
	{
		0.30, // float min_value;
		100.00, // float max_value;
		0.01, // float step_value;
		30.00, // float default_value;
		"Швидкість м/с при заході на ціль. При відсутності трубки Піто встановити значення 0..1, що відповідатиме % газу.Режим КАМІКАДЗЕ", // char description[300];
		false, // bool actual;
	},
};

#endif // CONSTRAINTS_H
