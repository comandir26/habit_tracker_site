export const demoDifficulties = [
  { value: 'easy', label: 'Лёгкая', base_xp: 10 },
  { value: 'medium', label: 'Средняя', base_xp: 20 },
  { value: 'hard', label: 'Сложная', base_xp: 30 },
]

export const weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

export function habitSchedule(habit) {
  return habit.schedule === 'daily' ? 'Каждый день' : habit.weekdays.map((day) => weekdays[day - 1]).join(', ')
}

export function validateHabit(data) {
  const errors = {}
  if (!data.name.trim()) errors.name = ['Введите название привычки.']
  else if (data.name.trim().length > 120) errors.name = ['Название должно содержать не больше 120 символов.']
  if (data.schedule === 'weekdays' && !data.weekdays.length) errors.weekdays = ['Выберите хотя бы один день.']
  if (!Number.isInteger(data.xp_weight) || data.xp_weight < 1 || data.xp_weight > 10) errors.xp_weight = ['Введите целый вес от 1 до 10.']
  return errors
}
