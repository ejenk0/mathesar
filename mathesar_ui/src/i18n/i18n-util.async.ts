// This file was auto-generated by 'typesafe-i18n'. Any manual changes will be overwritten.

import { initFormatters } from './formatters';
import type { Locales, Translations } from './i18n-types';
import { loadedFormatters, loadedLocales, locales } from './i18n-util';

const localeTranslationLoaders = {
  ja: () => import('./ja'),
  en: () => import('./en'),
};

const updateDictionary = (
  locale: Locales,
  dictionary: Partial<Translations>,
): Translations => {
  loadedLocales[locale] = { ...loadedLocales[locale], ...dictionary };
  return loadedLocales[locale];
};

export const importLocaleAsync = async (
  locale: Locales,
): Promise<Translations> =>
  (await localeTranslationLoaders[locale]()).default as unknown as Translations;

export const loadFormatters = (locale: Locales): void => {
  loadedFormatters[locale] = initFormatters(locale);
};

export const loadLocaleAsync = async (locale: Locales): Promise<void> => {
  updateDictionary(locale, await importLocaleAsync(locale));
  loadFormatters(locale);
};

export const loadAllLocalesAsync = (): Promise<void[]> =>
  Promise.all(locales.map(loadLocaleAsync));
