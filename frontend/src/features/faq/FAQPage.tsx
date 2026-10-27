import React, { useState, useEffect } from 'react';
import { HelpCircle, Search, ChevronDown, ChevronUp, Sparkles, MessageCircle, ArrowRight } from 'lucide-react';
import { api } from '../../services/api';
import type { FAQ, FAQCategory } from '../../types';

export const FAQPage: React.FC = () => {
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [categories, setCategories] = useState<FAQCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchFaqs = async () => {
    try {
      setLoading(true);
      const [faqData, catData] = await Promise.all([
        api.getFAQs({
          q: searchQuery || undefined,
          category: selectedCategory !== 'all' ? selectedCategory : undefined,
        }),
        api.getFAQCategories(),
      ]);
      setFaqs(faqData);
      setCategories(catData);
      if (faqData.length > 0 && !expandedId) {
        setExpandedId(faqData[0].id);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFaqs();
  }, [selectedCategory]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchFaqs();
  };

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto py-4">
      {/* Hero Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold">
          <HelpCircle className="h-3.5 w-3.5" />
          Knowledge Base & FAQ
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight sm:text-4xl">
          Frequently Asked Questions
        </h1>
        <p className="text-slate-400 text-sm max-w-xl mx-auto">
          Explore comprehensive guides on resume parsing, our hybrid scoring engine, privacy guarantees, and troubleshooting.
        </p>
      </div>

      {/* Search Input Bar */}
      <form onSubmit={handleSearchSubmit} className="relative max-w-xl mx-auto">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search question keywords (e.g. matching, score, PDF, tickets)..."
          className="w-full bg-slate-900 border border-slate-700 rounded-xl pl-11 pr-24 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 shadow-xl"
        />
        <Search className="h-5 w-5 text-slate-500 absolute left-3.5 top-3.5" />
        <button
          type="submit"
          className="absolute right-2 top-2 px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition-colors cursor-pointer"
        >
          Search
        </button>
      </form>

      {/* Category Pills Filter */}
      <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
        <button
          onClick={() => setSelectedCategory('all')}
          className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-colors ${
            selectedCategory === 'all'
              ? 'bg-indigo-600 text-white font-semibold shadow-md'
              : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
          }`}
        >
          All Topics ({faqs.length})
        </button>
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(cat.slug)}
            className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-colors ${
              selectedCategory === cat.slug
                ? 'bg-indigo-600 text-white font-semibold shadow-md'
                : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
            }`}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {/* Accordion FAQ List */}
      <div className="space-y-3 pt-2">
        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading questions from SQL database...</div>
        ) : faqs.length === 0 ? (
          <div className="p-12 text-center text-slate-500 glass-panel rounded-2xl">
            <HelpCircle className="h-8 w-8 mx-auto mb-2 text-slate-600" />
            <p className="text-sm font-semibold text-slate-300">No matching questions found</p>
            <p className="text-xs text-slate-400 mt-1">
              Try adjusting your search keywords, or ask our AI assistant below.
            </p>
          </div>
        ) : (
          faqs.map((faq) => {
            const isExpanded = expandedId === faq.id;
            return (
              <div
                key={faq.id}
                className="glass-panel border border-slate-800 rounded-xl overflow-hidden transition-all duration-200"
              >
                <button
                  onClick={() => toggleExpand(faq.id)}
                  className="w-full p-4 text-left flex items-center justify-between gap-4 hover:bg-slate-800/40 transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    {faq.category_name && (
                      <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shrink-0">
                        {faq.category_name}
                      </span>
                    )}
                    <span className="text-sm font-semibold text-white tracking-tight">
                      {faq.question}
                    </span>
                  </div>
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4 text-slate-400 shrink-0" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-slate-400 shrink-0" />
                  )}
                </button>

                {isExpanded && (
                  <div className="px-5 pb-5 pt-1 text-sm text-slate-300 border-t border-slate-800/60 leading-relaxed bg-slate-900/30">
                    {faq.answer}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* AI Assistant Callout Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-950/80 via-slate-900 to-slate-900 border border-indigo-500/30 flex flex-col sm:flex-row items-center justify-between gap-4 mt-8 shadow-xl">
        <div className="flex items-center gap-3.5">
          <div className="h-10 w-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shrink-0 shadow-lg shadow-indigo-600/30">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white">Have a specific question not listed here?</h4>
            <p className="text-xs text-slate-400 mt-0.5">
              Our AI Assistant is available 24/7 to answer application questions or escalate directly to engineering.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <a
            href="/support"
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-md"
          >
            <span>Open Support Ticket</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </a>
        </div>
      </div>
    </div>
  );
};
