import { useState, useRef, useEffect } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import {
  Upload,
  Loader2,
  Zap,
  Snowflake,
  Lightbulb,
  X,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { predictInspection } from '@/lib/api';

type Severity = 'critical' | 'warning' | 'normal';

interface Detection {
  id: string;
  label: 'Cracks' | 'Snow' | 'Dust' | 'Bird Droppings' | 'Clean';
  severity: Severity;
  confidence?: number;
  class_name?: string;

  box: {
    left: number;
    top: number;
    width: number;
    height: number;
  };
}

type RecTone = 'red' | 'blue' | 'amber';

interface Recommendation {
  title: string;
  description: string;
  priority: 'High Priority' | 'Medium Priority' | 'Low Priority';
  cta: string;
  icon: React.ReactNode;
  tone: RecTone;
}

const recTones: Record<
  RecTone,
  {
    card: string;
    iconWrap: string;
    pill: string;
    button: string;
  }
> = {
  red: {
    card:
      'border-red-500/40 bg-gradient-to-br from-red-950/40 via-[#1a0a10] to-[#0a0508]',
    iconWrap: 'text-red-400',
    pill: 'bg-red-500/15 text-red-400 border-red-500/40',
    button:
      'bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/40',
  },

  blue: {
    card:
      'border-blue-500/40 bg-gradient-to-br from-blue-950/40 via-[#0a1424] to-[#05080f]',
    iconWrap: 'text-blue-400',
    pill: 'bg-blue-500/15 text-blue-400 border-blue-500/40',
    button:
      'bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/40',
  },

  amber: {
    card:
      'border-amber-500/40 bg-gradient-to-br from-amber-950/30 via-[#1a1408] to-[#0a0805]',
    iconWrap: 'text-amber-400',
    pill: 'bg-amber-500/15 text-amber-400 border-amber-500/40',
    button:
      'bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/40',
  },
};

const severityStyles: Record<
  Severity,
  {
    dot: string;
    pill: string;
    border: string;
    label: string;
  }
> = {
  critical: {
    dot: 'bg-red-500',
    pill: 'bg-red-500/15 text-red-400 border-red-500/30',
    border: 'border-red-500/70',
    label: 'Critical',
  },

  warning: {
    dot: 'bg-amber-400',
    pill: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    border: 'border-amber-400/70',
    label: 'Warning',
  },

  normal: {
    dot: 'bg-cyan-400',
    pill: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
    border: 'border-cyan-400/70',
    label: 'Normal',
  },
};

const recommendations: Recommendation[] = [
  {
    title: 'Repair Cracked Panels',
    description:
      'Surface cracks compromise the panel and should be inspected.',

    priority: 'High Priority',
    cta: 'Dispatch Engineer',

    icon: <Zap className="w-5 h-5" />,
    tone: 'red',
  },

  {
    title: 'Clear Snow',
    description: 'Remove snow coverage from the panel surface.',

    priority: 'Medium Priority',
    cta: 'Schedule Cleaning',

    icon: <Snowflake className="w-5 h-5" />,
    tone: 'blue',
  },

  {
    title: 'Clean Panels',
    description: 'Remove dust or bird droppings.',

    priority: 'Medium Priority',
    cta: 'Schedule Cleaning',

    icon: <Lightbulb className="w-5 h-5" />,
    tone: 'amber',
  },
];

const UploadTab = () => {
  const { t } = useLanguage();
  const { toast } = useToast();

  const [isDragging, setIsDragging] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hasResult, setHasResult] = useState(false);

  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [outputUrl, setOutputUrl] = useState<string | null>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    handleFiles(e.dataTransfer.files);
  };

  const handleFileSelect = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = (files: FileList) => {
    if (files.length === 0) return;

    const file = files[0];

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setPreviewUrl(URL.createObjectURL(file));
    setSelectedFile(file);

    setHasResult(false);
  };

  const handleBrowse = () => {
    fileInputRef.current?.click();
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      handleBrowse();
      return;
    }

    setIsAnalyzing(true);
    setHasResult(false);

    try {
      const result = await predictInspection([selectedFile]);

      // ===== DETECTIONS =====

      const resultsArray = (result as any)?.results;

      if (resultsArray && Array.isArray(resultsArray) && resultsArray.length > 0) {
        // 1. الدخول لأول عنصر في الـ results
        const firstResult = resultsArray[0];
        
        // 2. الدخول للـ pipeline_data ومن ثم مصفوفة الـ detections الحقيقية
        const innerDetections = firstResult?.pipeline_data?.detections;

        if (innerDetections && Array.isArray(innerDetections)) {
          setDetections(
            innerDetections.map((d: any, index: number) => {
              // تحويل الإحداثيات إذا كانت نصاً أو كائناً قادماً من الباك إند
              const coords = typeof d.box_coordinates === 'string' 
                ? JSON.parse(d.box_coordinates) 
                : d.box_coordinates;

              const faultType = String(d.fault_type || '').toLowerCase();

              return {
                id: d.id?.toString() || (index + 1).toString(),

                label:
                  faultType.includes('crack')
                    ? 'Cracks'
                    : faultType.includes('dust')
                    ? 'Dust'
                    : faultType.includes('drop') || faultType.includes('bird')
                    ? 'Bird Droppings'
                    : faultType.includes('snow')
                    ? 'Snow'
                    : 'Clean',

                class_name: d.fault_type || 'unknown',

                severity:
                  (d.confidence || 0) >= 0.85
                    ? 'critical'
                    : (d.confidence || 0) >= 0.6
                    ? 'warning'
                    : 'normal',

                confidence: d.confidence !== undefined ? d.confidence : 0,

                box: {
                  left: coords?.x1 || 0,
                  top: coords?.y1 || 0,
                  width: (coords?.x2 || 0) - (coords?.x1 || 0),
                  height: (coords?.y2 || 0) - (coords?.y1 || 0),
                },
              };
            })
          );
        } else {
          // إذا كانت مصفوفة الـ detections فاضية معناها اللوحة نظيفة
          setDetections([]);
        }
      }

      // ===== OUTPUT IMAGE =====
      const resultsArrayForImage = (result as any)?.results;

      if (resultsArrayForImage && Array.isArray(resultsArrayForImage) && resultsArrayForImage.length > 0) {
        const outputResult = resultsArrayForImage[0];
        const outputPath = outputResult?.pipeline_data?.output_path;

        if (outputPath) {
           const fileName = outputPath.substring(outputPath.lastIndexOf('/') + 1);
         setOutputUrl(
           `http://localhost:8000/ai_outputs/${fileName}`
          );
        }
      }

      setHasResult(true);
    } catch (err) {
      console.error('Inspection prediction failed:', err);

      const description =
        err instanceof Error
          ? err.message
          : typeof err === 'string'
          ? err
          : JSON.stringify(err);

      toast({
        title: 'Analysis failed',
        description,
        variant: 'destructive',
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleClear = () => {
    setHasResult(false);
    setIsAnalyzing(false);

    setSelectedFile(null);
    setDetections([]);
    setOutputUrl(null);

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setPreviewUrl(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const showImageState = isAnalyzing || hasResult;

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.04] to-white/[0.01] backdrop-blur-sm p-6 flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-foreground">
            {showImageState
              ? t.analysisResults || 'Analysis Result'
              : t.uploadFiles || 'Upload File'}
          </h3>

          {hasResult && !isAnalyzing && (
            <button
              onClick={handleClear}
              className="w-7 h-7 rounded-full bg-white/5 hover:bg-red-500/20 border border-white/10"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {isAnalyzing ? (
          <div className="border-2 border-dashed border-cyan-500/20 rounded-xl flex-1 flex items-center justify-center min-h-[360px]">
            <div className="text-center">
              <Loader2 className="w-16 h-16 mx-auto text-primary animate-spin mb-4" />

              <p className="text-muted-foreground">
                Analyzing image...
              </p>
            </div>
          </div>
        ) : hasResult ? (
          <div className="relative rounded-xl overflow-hidden border border-white/10 mx-auto w-full max-w-[640px] bg-black">
            {outputUrl && outputUrl.endsWith(".mp4") ? (
              <video
               controls
               autoPlay
               onError={(e) => console.log("VIDEO ERROR", e)}
               onLoadedData={() => console.log("VIDEO LOADED")}
               className="w-full h-[320px] object-contain"
            >
               <source src={outputUrl} type="video/mp4" />
            </video>
          ) : (
            <img
              src={outputUrl || previewUrl || ""}
              alt="Analyzed solar panel"
              className="w-full h-[320px] object-contain"
            />
          )}
          </div>
        ) : (
          <>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors flex-1 flex flex-col items-center justify-center min-h-[360px] ${
                isDragging
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:border-primary/50'
              }`}
            >
              <Upload className="w-12 h-12 mx-auto text-muted-foreground mb-4" />

              <p className="text-foreground font-medium mb-2">
                {t.dropFilesHere}
              </p>

              <p className="text-sm text-muted-foreground mb-4">
                {t.supportedFormat}
              </p>

              <button
                onClick={handleBrowse}
                className="text-primary hover:underline font-medium"
              >
                {t.browseFiles}
              </button>

              <input
                ref={fileInputRef}
                type="file"
                accept="image/,video/,.pdf,.doc,.docx"
                multiple
                onChange={handleFileSelect}
                className="hidden"
              />
            </div>

            {selectedFile && (
              <p className="text-xs text-muted-foreground mt-3 truncate">
                Selected:{' '}
                <span className="text-foreground">
                  {selectedFile.name}
                </span>
              </p>
            )}

            <Button
              className="w-full mt-4"
              disabled={isAnalyzing || !selectedFile}
              onClick={handleAnalyze}
            >
              {isAnalyzing
                ? 'Analyzing...'
                : 'Analyze File '}
            </Button>
          </>
        )}
      </div>

      {hasResult && !isAnalyzing && (
        <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.04] to-white/[0.01] backdrop-blur-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm font-semibold text-foreground">
              Detection Summary
            </p>

            <span className="text-xs text-muted-foreground">
              {detections.length} detections
            </span>
          </div>

          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wider text-muted-foreground border-b border-white/5">
                <th className="py-2.5 px-3 font-medium">
                  ID
                </th>

                <th className="py-2.5 px-3 font-medium">
                  Type
                </th>

                <th className="py-2.5 px-3 font-medium">
                  Confidence
                </th>
              </tr>
            </thead>

            <tbody>
              {detections.map((d, i) => {
                const s = severityStyles[d.severity];

                return (
                  <tr
                    key={i}
                    className="border-b border-white/5 last:border-0 hover:bg-white/[0.02] transition-colors"
                  >
                    <td className="py-3 px-3 text-foreground font-mono text-xs">
                      {i + 1}
                    </td>

                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <span
                          className={`w-2 h-2 rounded-full ${s.dot}`}
                        />

                        <span className="text-foreground">
                          {d.label ||
                            d.class_name ||
                            'Unknown'}
                        </span>
                      </div>
                    </td>

                    <td className="py-3 px-3">
                      <span
                        className={`inline-block text-[11px] px-2.5 py-1 rounded-full border ${s.pill}`}
                      >
                        {Math.round(
                          (d.confidence || 0) * 100
                        )}
                        %
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default UploadTab;
