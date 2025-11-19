from typing import List
from fastapi import HTTPException


class Calculator:
    def sum_specific_elements(self, answers: List[int], indices: List[int]) -> int:
        return sum(answers[i - 1] for i in indices)

    def check_number_responses(self, len_res, answers_cnt):
        if len_res != answers_cnt:
            raise HTTPException(status_code=400,
                                detail="Передано неверное количество ответов")

    def test_maslach_calculate_results(self, answers: List[int]):
        indices_1 = [1, 2, 3, 6, 8, 13, 14, 16, 20]
        indices_2 = [5, 10, 11, 15, 22]
        indices_3 = [4, 7, 9, 12, 17, 18, 19, 21]
        scale_1_sum = calculator_service.sum_specific_elements(answers, indices_1)
        scale_2_sum = calculator_service.sum_specific_elements(answers, indices_2)
        scale_3_sum = calculator_service.sum_specific_elements(answers, indices_3)
        return [scale_1_sum, scale_2_sum, scale_3_sum]

    def test_jas_calculate_results(self, answers: List[int]):
        indices_1 = [1, 2, 3, 4, 5]
        indices_2 = [6, 7, 8, 9, 10]
        scale_1_sum = sum(answers)
        scale_2_sum = calculator_service.sum_specific_elements(answers, indices_1)
        scale_3_sum = calculator_service.sum_specific_elements(answers, indices_2)
        return [scale_1_sum, scale_2_sum, scale_3_sum]

    def test_dass21_calculate_results(self, answers: List[int]):
        indices_1 = [2, 4, 7, 9, 15, 19, 20]
        indices_2 = [3, 5, 10, 13, 16, 17, 21]
        indices_3 = [1, 6, 8, 11, 12, 14, 18]
        scale_1_sum = calculator_service.sum_specific_elements(answers, indices_1)
        scale_2_sum = calculator_service.sum_specific_elements(answers, indices_2)
        scale_3_sum = calculator_service.sum_specific_elements(answers, indices_3)
        return [scale_1_sum, scale_2_sum, scale_3_sum]

    def test_stai_calculate_results(self, answers: List[int]):
        indices_1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        indices_2 = [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40]
        scale_1_sum = calculator_service.sum_specific_elements(answers, indices_1)
        scale_2_sum = calculator_service.sum_specific_elements(answers, indices_2)
        return [scale_1_sum, scale_2_sum]

    def test_cmq_calculate_results(self, answers: List[int]):
        indices_2 = [20, 16, 15, 19, 13]
        indices_3 = [14, 8, 17, 6, 9]
        indices_4 = [43, 44, 42, 45, 23]
        indices_5 = [11, 12, 39, 40, 21]
        indices_6 = [3, 1, 2, 10, 25]
        indices_7 = [26, 38, 4, 5, 36, 35, 34, 29, 28]
        indices_8 = [22, 24, 18, 21, 25, 23]
        indices_9 = [33, 34, 35, 23, 9, 31, 27]
        indices_10 = [37, 40, 32, 33, 41]
        scale_1_sum = sum(answers)
        scale_2_sum = round(calculator_service.sum_specific_elements(answers, indices_2) / len(indices_2), 2)
        scale_3_sum = round(calculator_service.sum_specific_elements(answers, indices_3) / len(indices_3), 2)
        scale_4_sum = round(calculator_service.sum_specific_elements(answers, indices_4) / len(indices_4), 2)
        scale_5_sum = round(calculator_service.sum_specific_elements(answers, indices_5) / len(indices_5), 2)
        scale_6_sum = round(calculator_service.sum_specific_elements(answers, indices_6) / len(indices_6), 2)
        scale_7_sum = round(calculator_service.sum_specific_elements(answers, indices_7) / len(indices_7), 2)
        scale_8_sum = round(calculator_service.sum_specific_elements(answers, indices_8) / len(indices_8), 2)
        scale_9_sum = round(calculator_service.sum_specific_elements(answers, indices_9) / len(indices_9), 2)
        scale_10_sum = round(calculator_service.sum_specific_elements(answers, indices_10) / len(indices_10), 2)
        return [scale_1_sum, scale_2_sum, scale_3_sum, scale_4_sum, scale_5_sum, scale_6_sum, scale_7_sum, scale_8_sum,
                scale_9_sum, scale_10_sum]

    def test_coling_calculate_results(self, answers: List[int]):
        indices_1 = [2, 3, 8, 9, 11, 15, 16, 17, 20, 29, 33]
        indices_2 = [1, 5, 7, 12, 14, 19, 23, 24, 25, 31, 32]
        indices_3 = [4, 6, 10, 13, 18, 21, 22, 26, 27, 28, 30]
        scale_1_sum = calculator_service.sum_specific_elements(answers, indices_1)
        scale_2_sum = calculator_service.sum_specific_elements(answers, indices_2)
        scale_3_sum = calculator_service.sum_specific_elements(answers, indices_3)
        return [scale_1_sum, scale_2_sum, scale_3_sum]

    def test_back_calculate_results(self, answers: List[int]):
        indices_1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
        indices_2 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        indices_3 = [14, 15, 16, 17, 18, 19, 20, 21]
        scale_1_sum = calculator_service.sum_specific_elements(answers, indices_1)
        scale_2_sum = calculator_service.sum_specific_elements(answers, indices_2)
        scale_3_sum = calculator_service.sum_specific_elements(answers, indices_3)
        return [scale_1_sum, scale_2_sum, scale_3_sum]

    def test_stress_calculate_results(self, answers: List[int]):
        indices_1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        indices_2 = [1, 2, 3, 6, 9, 10]
        indices_3 = [4, 5, 7, 8]
        scale_1_sum = calculator_service.sum_specific_elements(answers, indices_1)
        scale_2_sum = calculator_service.sum_specific_elements(answers, indices_2)
        scale_3_sum = calculator_service.sum_specific_elements(answers, indices_3)
        return [scale_1_sum, scale_2_sum, scale_3_sum]

    def test_leasy_calculate_results(self, answers: List[int]):
        self.check_number_responses(len(answers), 28)

        def calculate_scale(positive_indices, reverse_indices=[]):
            total = 0
            if positive_indices:
                total += self.sum_specific_elements(answers, positive_indices)
            if reverse_indices:
                reverse_sum = self.sum_specific_elements(answers, reverse_indices)
                total += (7 * len(reverse_indices) - reverse_sum)
            total_count = len(positive_indices) + len(reverse_indices)
            return round(total / total_count, 2) if total_count > 0 else 0

        invalidation = calculate_scale([6, 12], [])
        incomprehensibility = calculate_scale([3, 7], [])
        guilt_shame = calculate_scale([2, 10], [])
        simplistic_view = calculate_scale([23, 28], [])
        devaluation = calculate_scale([], [14, 26])
        loss_of_control = calculate_scale([5, 17], [])
        numbness = calculate_scale([11, 20], [])
        over_rationality = calculate_scale([13, 27], [])
        duration = calculate_scale([9], [19])
        low_consensus = calculate_scale([1], [25])
        non_acceptance = calculate_scale([18], [24])
        rumination = calculate_scale([22, 16], [])
        low_expression = calculate_scale([], [4, 15])
        blame = calculate_scale([8, 21], [])

        return [
            invalidation, incomprehensibility, guilt_shame, simplistic_view,
            devaluation, loss_of_control, numbness, over_rationality,
            duration, low_consensus, non_acceptance, rumination,
            low_expression, blame
        ]

calculator_service = Calculator()
