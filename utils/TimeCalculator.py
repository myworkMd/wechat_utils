from datetime import datetime, timedelta
import calendar
from typing import Optional, Union


class TimeCalculator:
    """
    多功能时间计算工具，明确区分增量时间和固定时间设置，输出格式化为YYYY-MM-DD HH:MM:SS

    参数命名规则：
    - delta_xxx: 表示时间增量（可正可负）
    - fixed_xxx: 表示设置固定的时间部分

    示例用法：
    1. TimeCalculator.calculate(delta_days=10)  # 10天后
    2. TimeCalculator.calculate(delta_months=1, fixed_day=10)  # 1个月后的10号
    3. TimeCalculator.calculate(delta_months=1, delta_days=10)  # 1个月+10天后
    4. TimeCalculator.calculate(fixed_hour=8, fixed_minute=30)  # 设置为今天的8:30
    """

    @staticmethod
    def calculate(
            base_time: Optional[datetime] = None,
            # 增量参数
            delta_years: int = 0,
            delta_months: int = 0,
            delta_weeks: int = 0,
            delta_days: int = 0,
            delta_hours: int = 0,
            delta_minutes: int = 0,
            delta_seconds: int = 0,
            # 固定值参数
            fixed_year: Optional[int] = None,
            fixed_month: Optional[int] = None,
            fixed_day: Optional[int] = None,
            fixed_weekday: Optional[int] = None,  # 0=周一，6=周日
            fixed_hour: Optional[int] = None,
            fixed_minute: Optional[int] = None,
            fixed_second: Optional[int] = None,
            # 输出格式控制
            as_string: bool = True,
            fmt: str = "%Y-%m-%d %H:%M:%S"
    ) -> Union[datetime, str]:
        """
        最终完善版本计算方法
        """
        if base_time is None:
            base_time = datetime.now()

        # 第一步：处理所有时间增量
        result = base_time + timedelta(
            weeks=delta_weeks,
            days=delta_days,
            hours=delta_hours,
            minutes=delta_minutes,
            seconds=delta_seconds
        )

        # 处理年和月的增量
        if delta_years != 0 or delta_months != 0:
            result = TimeCalculator._add_months(result, delta_years * 12 + delta_months)

        # 第二步：处理固定日期/时间（除星期几外）
        if fixed_year is not None:
            result = result.replace(year=fixed_year)
        if fixed_month is not None:
            result = result.replace(month=fixed_month)
        if fixed_day is not None:
            last_day = TimeCalculator._get_last_day_of_month(result)
            result = result.replace(day=min(fixed_day, last_day))
        if fixed_hour is not None:
            result = result.replace(hour=fixed_hour)
        if fixed_minute is not None:
            result = result.replace(minute=fixed_minute)
        if fixed_second is not None:
            result = result.replace(second=fixed_second)

        # 第三步：处理星期几（智能跳周逻辑）
        if fixed_weekday is not None:
            current_weekday = result.weekday()
            days_diff = fixed_weekday - current_weekday

            # 检测是否存在时间增量
            has_delta = any([
                delta_years, delta_months, delta_weeks, delta_days,
                delta_hours, delta_minutes, delta_seconds
            ])

            # 没有增量参数且目标日期已过时，跳到下周
            if not has_delta and days_diff <= 0:
                days_diff += 7

            result += timedelta(days=days_diff)

        return result.strftime(fmt) if as_string else result

    @staticmethod
    def _add_months(dt: datetime, months: int) -> datetime:
        """处理增加月份的逻辑（内部方法）"""
        month = dt.month - 1 + months
        year = dt.year + month // 12
        month = month % 12 + 1
        day = min(dt.day, TimeCalculator._get_last_day_of_month(datetime(year, month, 1)))
        return dt.replace(year=year, month=month, day=day)

    @staticmethod
    def _get_last_day_of_month(dt: datetime) -> int:
        """获取某个月的最后一天（内部方法）"""
        return calendar.monthrange(dt.year, dt.month)[1]


if __name__ == '__main__':
    # 示例2：1个月后的10号
    print("1个月后的10号:", TimeCalculator.calculate(delta_months=1, fixed_day=10))

    # 示例3：当前时间设置为下午3点
    print("设置为下午3点:", TimeCalculator.calculate(fixed_hour=15, fixed_minute=0))

    # 示例4：3年2个月后的6月15日9点30分
    print("3年2个月后的6月15日9点30分:",
          TimeCalculator.calculate(
              delta_years=3,
              delta_months=2,
              fixed_month=6,
              fixed_day=15,
              fixed_hour=9,
              fixed_minute=30
          ))

    # 示例5：获取datetime对象而非字符串
    dt_obj = TimeCalculator.calculate(delta_days=5, as_string=False)
    print("5天后的datetime对象:", dt_obj)
    print("格式化后的字符串:", dt_obj.strftime("%Y-%m-%d %H:%M:%S"))

    # 示例6：自定义输出格式
    print("自定义格式:", TimeCalculator.calculate(delta_hours=12, fmt="%Y/%m/%d %H时%M分"))

    print(f"明天10点:{TimeCalculator.calculate(delta_days=1,fixed_hour=10,fixed_minute=0,fixed_second=0)}")
    # 示例1：下周三（假设今天是2023-07-18周二）
    print("下周三:", TimeCalculator.calculate(delta_weeks=0, fixed_weekday=2))  # 2023-07-19
