"use client";

import * as React from "react";
import { useFlashcards } from "@/hooks/use-flashcards";
import { Button } from "@/components/ui/button";
import { Sparkles, Layers, ChevronLeft, ChevronRight, RefreshCw, Eye, Download, Star, RotateCcw, Filter, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { useDocuments } from "@/hooks/use-documents";

interface FlashcardPanelProps {
  selectedDocumentIds: string[];
}

export function FlashcardPanel({ selectedDocumentIds }: FlashcardPanelProps) {
  const { data: allDocsResponse } = useDocuments();
  const allDocs = allDocsResponse?.items ?? [];
  
  // Resolve documents to use: selected or all
  const effectiveDocs = selectedDocumentIds.length > 0 ? selectedDocumentIds : allDocs.map(d => d.id);
  const { flashcards, isGenerating, generateFlashcards, deleteFlashcard, updateFlashcard } = useFlashcards(
    selectedDocumentIds.length === 1 ? selectedDocumentIds[0] : undefined
  );

  const [currentIndex, setCurrentIndex] = React.useState(0);
  const [isFlipped, setIsFlipped] = React.useState(false);
  const [generateCount, setGenerateCount] = React.useState(5);
  const [filterMode, setFilterMode] = React.useState<'all' | 'starred' | 'hard'>('all');
  const [shuffledList, setShuffledList] = React.useState<typeof flashcards | null>(null);

  const studyCards = React.useMemo(() => {
    let list = shuffledList || flashcards;
    if (filterMode === 'starred') {
      list = list.filter(c => c.is_starred);
    } else if (filterMode === 'hard') {
      list = list.filter(c => c.difficulty === 'hard');
    }
    return list;
  }, [flashcards, shuffledList, filterMode]);

  const activeCard = studyCards[currentIndex];

  React.useEffect(() => {
    if (currentIndex >= studyCards.length) {
      setCurrentIndex(0);
    }
  }, [studyCards.length, currentIndex]);

  const handleFlip = () => setIsFlipped((prev) => !prev);

  const handleNext = () => {
    setIsFlipped(false);
    setTimeout(() => {
      setCurrentIndex((prev) => (prev + 1) % studyCards.length);
    }, 150);
  };

  const handlePrev = () => {
    setIsFlipped(false);
    setTimeout(() => {
      setCurrentIndex((prev) => (prev - 1 + studyCards.length) % studyCards.length);
    }, 150);
  };

  const handleShuffle = () => {
    setIsFlipped(false);
    const shuffled = [...flashcards].sort(() => Math.random() - 0.5);
    setShuffledList(shuffled);
    setCurrentIndex(0);
    toast.success("Deck shuffled!");
  };

  const handleReset = () => {
    setIsFlipped(false);
    setShuffledList(null);
    setFilterMode('all');
    setCurrentIndex(0);
    toast.success("Deck reset!");
  };

  const handleGenerate = async () => {
    if (effectiveDocs.length === 0) {
      toast.error("Please upload or select at least one document first.");
      return;
    }
    try {
      await generateFlashcards({
        document_ids: effectiveDocs,
        count: generateCount,
        model: "llama3"
      });
      setCurrentIndex(0);
      setIsFlipped(false);
      setShuffledList(null);
    } catch {
      // Error is already handled by hook toast
    }
  };

  const updateCardDifficulty = async (difficulty: "easy" | "medium" | "hard") => {
    if (!activeCard) return;
    try {
      await updateFlashcard(activeCard.id, { difficulty });
      toast.success(`Marked as ${difficulty}`);
    } catch (e) {
      console.error(e);
    }
  };

  const toggleStar = async (card: typeof activeCard, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await updateFlashcard(card.id, { is_starred: !card.is_starred });
      toast.success(card.is_starred ? "Removed star" : "Starred card!");
    } catch (e) {
      console.error(e);
    }
  };

  const handleExport = (type: "json" | "csv") => {
    if (studyCards.length === 0) {
      toast.error("No flashcards to export.");
      return;
    }

    let dataStr = "";
    let mimeType = "";
    let filename = "";

    if (type === "json") {
      dataStr = JSON.stringify(studyCards, null, 2);
      mimeType = "application/json";
      filename = "flashcards-export.json";
    } else {
      dataStr = "Front,Back,Difficulty,Starred\n" + studyCards.map(
        c => `"${c.front.replace(/"/g, '""')}","${c.back.replace(/"/g, '""')}","${c.difficulty}","${c.is_starred ? 'yes' : 'no'}"`
      ).join("\n");
      mimeType = "text/csv";
      filename = "flashcards-export.csv";
    }

    const blob = new Blob([dataStr], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex h-full flex-col space-y-4">
      {/* Header / Config Controls */}
      <div className="rounded-xl border border-border/40 bg-[var(--assistant-bubble)] p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <Layers className="h-4 w-4 text-indigo-500" />
            AI Flashcard Study Deck
          </div>
          {flashcards.length > 0 && (
            <div className="flex items-center gap-1">
              <Button
                onClick={() => setFilterMode('all')}
                size="sm"
                variant={filterMode === 'all' ? 'default' : 'ghost'}
                className="h-6 text-[10px] px-2 rounded-md"
              >
                All
              </Button>
              <Button
                onClick={() => setFilterMode('starred')}
                size="sm"
                variant={filterMode === 'starred' ? 'default' : 'ghost'}
                className="h-6 text-[10px] px-2 rounded-md flex items-center gap-1 text-amber-400"
              >
                <Star className="h-2.5 w-2.5 fill-current" /> Starred
              </Button>
              <Button
                onClick={() => setFilterMode('hard')}
                size="sm"
                variant={filterMode === 'hard' ? 'default' : 'ghost'}
                className="h-6 text-[10px] px-2 rounded-md flex items-center gap-1 text-rose-400"
              >
                <AlertTriangle className="h-2.5 w-2.5" /> Hard Ones
              </Button>
            </div>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          Generate Q&A flashcards using local AI from selected documents.
        </p>

        <div className="flex items-center gap-2 pt-1">
          <div className="flex flex-1 items-center gap-1.5 rounded-lg bg-[var(--border-color)] px-2.5 py-1.5 border border-transparent">
            <span className="text-xs text-muted-foreground">Count:</span>
            <input
              type="number"
              value={generateCount}
              onChange={(e) => setGenerateCount(Math.max(1, Math.min(20, parseInt(e.target.value) || 5)))}
              className="w-12 bg-transparent text-center text-xs font-semibold text-white focus:outline-none"
            />
          </div>

          <Button
            onClick={handleGenerate}
            disabled={isGenerating || effectiveDocs.length === 0}
            size="sm"
            className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-medium"
          >
            {isGenerating ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <>
                <Sparkles className="mr-1.5 h-3.5 w-3.5" />
                Generate
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Main Flashcard View */}
      {studyCards.length > 0 && activeCard ? (
        <div className="flex-1 flex flex-col space-y-3 min-h-0">
          {/* Card perspective container */}
          <div 
            onClick={handleFlip}
            className="flex-1 min-h-[220px] max-h-[350px] relative cursor-pointer select-none card-perspective group"
          >
            {/* Inner flippable box */}
            <div className={`card-inner ${isFlipped ? "flipped" : ""} w-full h-full relative rounded-2xl border border-border/40 bg-[var(--assistant-bubble)] p-6 shadow-md flex flex-col items-center justify-center text-center`}>
              
              {/* Front side */}
              <div className="card-face absolute inset-0 flex flex-col justify-between p-6">
                <div className="flex justify-between items-center w-full text-[10px] tracking-wider uppercase text-indigo-400 font-semibold">
                  <span>Card {currentIndex + 1} of {studyCards.length}</span>
                  <div className="flex items-center gap-1.5">
                    <span className="bg-indigo-500/10 px-2 py-0.5 rounded-full">{activeCard.difficulty}</span>
                    <button
                      onClick={(e) => toggleStar(activeCard, e)}
                      className="p-1 rounded-full hover:bg-white/10 text-amber-400"
                    >
                      <Star className={`h-4.5 w-4.5 ${activeCard.is_starred ? 'fill-current' : ''}`} />
                    </button>
                  </div>
                </div>
                
                <div className="flex-1 flex items-center justify-center">
                  <h3 className="text-sm font-semibold text-white leading-relaxed px-4">
                    {activeCard.front}
                  </h3>
                </div>

                <div className="text-[10px] text-muted-foreground flex items-center justify-center gap-1">
                  <Eye className="h-3 w-3" /> Click card to reveal answer
                </div>
              </div>

              {/* Back side */}
              <div className="card-face card-back absolute inset-0 flex flex-col justify-between p-6 bg-indigo-950/20 border border-indigo-500/30 rounded-2xl">
                <div className="flex justify-between items-center w-full text-[10px] tracking-wider uppercase text-indigo-400 font-semibold">
                  <span>Answer</span>
                  <div className="flex items-center gap-1.5">
                    <span className="bg-indigo-500/10 px-2 py-0.5 rounded-full">{activeCard.difficulty}</span>
                    <button
                      onClick={(e) => toggleStar(activeCard, e)}
                      className="p-1 rounded-full hover:bg-white/10 text-amber-400"
                    >
                      <Star className={`h-4.5 w-4.5 ${activeCard.is_starred ? 'fill-current' : ''}`} />
                    </button>
                  </div>
                </div>

                <div className="flex-1 flex items-center justify-center overflow-y-auto px-2 my-2">
                  <p className="text-xs text-muted-foreground text-center leading-relaxed">
                    {activeCard.back}
                  </p>
                </div>

                {/* Difficulty selectors on reveal */}
                <div className="flex justify-center gap-1.5 pt-2">
                  <Button 
                    onClick={(e) => { e.stopPropagation(); updateCardDifficulty("easy"); }}
                    size="icon" variant="ghost" className="h-6 px-2 text-[10px] rounded hover:bg-emerald-500/20 text-emerald-400"
                  >
                    Easy
                  </Button>
                  <Button 
                    onClick={(e) => { e.stopPropagation(); updateCardDifficulty("medium"); }}
                    size="icon" variant="ghost" className="h-6 px-2 text-[10px] rounded hover:bg-amber-500/20 text-amber-400"
                  >
                    Medium
                  </Button>
                  <Button 
                    onClick={(e) => { e.stopPropagation(); updateCardDifficulty("hard"); }}
                    size="icon" variant="ghost" className="h-6 px-2 text-[10px] rounded hover:bg-rose-500/20 text-rose-400"
                  >
                    Hard
                  </Button>
                </div>
              </div>

            </div>
          </div>

          <style dangerouslySetInnerHTML={{__html: `
            .card-perspective {
              perspective: 1000px;
            }
            .card-inner {
              position: relative;
              width: 100%;
              height: 100%;
              transition: transform 0.6s;
              transform-style: preserve-3d;
            }
            .card-inner.flipped {
              transform: rotateY(180deg);
            }
            .card-face {
              position: absolute;
              inset: 0;
              backface-visibility: hidden;
              -webkit-backface-visibility: hidden;
            }
            .card-back {
              transform: rotateY(180deg);
            }
          `}} />

          {/* Navigation & Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1">
              <Button size="icon" variant="ghost" className="h-8 w-8 text-white rounded-lg hover:bg-[var(--border-color)]" onClick={handlePrev}>
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-xs font-semibold text-muted-foreground w-12 text-center">
                {currentIndex + 1} / {studyCards.length}
              </span>
              <Button size="icon" variant="ghost" className="h-8 w-8 text-white rounded-lg hover:bg-[var(--border-color)]" onClick={handleNext}>
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>

            <div className="flex items-center gap-1.5">
              <Button size="icon" variant="ghost" className="h-8 w-8 text-indigo-400 rounded-lg hover:bg-indigo-500/10" title="Shuffle Deck" onClick={handleShuffle}>
                <RefreshCw className="h-3.5 w-3.5" />
              </Button>
              <Button size="icon" variant="ghost" className="h-8 w-8 text-amber-400 rounded-lg hover:bg-amber-500/10" title="Reset Deck" onClick={handleReset}>
                <RotateCcw className="h-3.5 w-3.5" />
              </Button>
              <Button size="icon" variant="ghost" className="h-8 w-8 text-muted-foreground rounded-lg hover:bg-destructive/10 hover:text-destructive" title="Delete Card" onClick={() => deleteFlashcard(activeCard.id).then(() => setCurrentIndex(0))}>
                <Layers className="h-3.5 w-3.5" />
              </Button>
              
              <div className="h-4 w-px bg-border/40 mx-0.5" />

              <Button size="icon" variant="ghost" className="h-8 w-8 text-indigo-400 rounded-lg hover:bg-indigo-500/10" title="Export as CSV" onClick={() => handleExport("csv")}>
                <Download className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center border border-dashed border-border/40 rounded-xl p-8 text-center bg-[var(--assistant-bubble)]/40 min-h-[220px]">
          <Layers className="h-8 w-8 text-muted-foreground mb-2" />
          <p className="text-sm font-medium text-white/95">
            {filterMode !== 'all' ? "No Matching Flashcards" : "No Study Flashcards"}
          </p>
          <p className="text-xs text-muted-foreground mt-1 max-w-[200px]">
            {filterMode !== 'all' ? "Try changing your filter settings or reset your deck." : "Generate cards to study key facts and concepts."}
          </p>
          {filterMode !== 'all' && (
            <Button size="sm" onClick={handleReset} className="mt-3 bg-indigo-600 hover:bg-indigo-700 text-white">
              Reset Filters
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
